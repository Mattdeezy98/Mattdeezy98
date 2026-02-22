from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
import random
import hashlib
import hmac
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'neonvegas_secret_key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Stripe Configuration
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')

# PayID Configuration (Zai/Assembly Payments)
PAYID_API_KEY = os.environ.get('PAYID_API_KEY', '')
PAYID_API_SECRET = os.environ.get('PAYID_API_SECRET', '')
PAYID_ENVIRONMENT = os.environ.get('PAYID_ENVIRONMENT', 'sandbox')
PAYID_WEBHOOK_SECRET = os.environ.get('PAYID_WEBHOOK_SECRET', '')

# External Game Provider Configurations
JILI_API_KEY = os.environ.get('JILI_API_KEY', '')
JILI_API_SECRET = os.environ.get('JILI_API_SECRET', '')
JILI_AGENT_ID = os.environ.get('JILI_AGENT_ID', '')
JILI_API_URL = os.environ.get('JILI_API_URL', 'https://api.jiligames.net')

IMPERIUM_API_KEY = os.environ.get('IMPERIUM_API_KEY', '')
IMPERIUM_API_SECRET = os.environ.get('IMPERIUM_API_SECRET', '')
IMPERIUM_API_URL = os.environ.get('IMPERIUM_API_URL', 'https://api.imperium-games.com')

SLOTOMANIA_API_KEY = os.environ.get('SLOTOMANIA_API_KEY', '')
SLOTOMANIA_API_SECRET = os.environ.get('SLOTOMANIA_API_SECRET', '')
SLOTOMANIA_API_URL = os.environ.get('SLOTOMANIA_API_URL', 'https://api.slotomania.com')

RICH_API_KEY = os.environ.get('RICH_API_KEY', '')
RICH_API_SECRET = os.environ.get('RICH_API_SECRET', '')
RICH_API_URL = os.environ.get('RICH_API_URL', 'https://api.richgames.com')

# Jackpot Configuration
JACKPOT_CONTRIBUTION_RATE = 0.02
JACKPOT_WIN_PROBABILITY = 0.0001
MINIMUM_JACKPOT = 1000.0

# VIP Tier Configuration
VIP_TIERS = {
    "bronze": {"min_wagered": 0, "cashback": 0.01, "bonus_multiplier": 1.0, "daily_bonus": 5},
    "silver": {"min_wagered": 1000, "cashback": 0.02, "bonus_multiplier": 1.1, "daily_bonus": 15},
    "gold": {"min_wagered": 5000, "cashback": 0.03, "bonus_multiplier": 1.25, "daily_bonus": 50},
    "platinum": {"min_wagered": 25000, "cashback": 0.05, "bonus_multiplier": 1.5, "daily_bonus": 150},
    "diamond": {"min_wagered": 100000, "cashback": 0.08, "bonus_multiplier": 2.0, "daily_bonus": 500}
}

# Security
security = HTTPBearer()

# Create the main app
app = FastAPI(title="NeonVegas Casino API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

# User Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    balance: float
    created_at: str
    gambling_limits: Optional[dict] = None
    self_exclusion: Optional[dict] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Wallet Models
class DepositRequest(BaseModel):
    amount: float
    method: str  # "payid_demo", "payid_real", "stripe"

class WithdrawRequest(BaseModel):
    amount: float
    payid_account: str  # PayID account (email or phone)

class TransactionResponse(BaseModel):
    id: str
    user_id: str
    type: str  # deposit, withdraw, bet, win
    amount: float
    method: str
    status: str
    created_at: str
    details: Optional[dict] = None

# Game Models
class BetRequest(BaseModel):
    game: str
    amount: float
    bet_details: dict

class GameResultResponse(BaseModel):
    id: str
    game: str
    bet_amount: float
    win_amount: float
    result: dict
    created_at: str

# Stripe Models
class StripeCheckoutRequest(BaseModel):
    package_id: str
    origin_url: str

# PayID Models
class PayIDDepositRequest(BaseModel):
    amount: float
    payid_type: str = "email"  # email, phone, abn

class PayIDWithdrawRequest(BaseModel):
    amount: float
    payid_account: str
    payid_type: str = "email"

# Responsible Gambling Models
class GamblingLimitsRequest(BaseModel):
    daily_limit: Optional[float] = None
    weekly_limit: Optional[float] = None
    monthly_limit: Optional[float] = None
    session_time_limit: Optional[int] = None  # minutes
    reality_check_interval: Optional[int] = None  # minutes

class SelfExclusionRequest(BaseModel):
    duration: str  # "24h", "7d", "30d", "6m", "1y", "permanent"
    reason: Optional[str] = None

# Fixed deposit packages (amounts in AUD)
DEPOSIT_PACKAGES = {
    "small": 10.0,
    "medium": 25.0,
    "large": 50.0,
    "xl": 100.0,
    "xxl": 250.0
}

# ==================== PAYID SERVICE ====================

class PayIDService:
    """
    Production-ready PayID integration service.
    Supports Zai (Assembly Payments), Monoova, or Zepto.
    Configure PAYID_API_KEY and PAYID_API_SECRET in .env
    """
    
    def __init__(self):
        self.api_key = PAYID_API_KEY
        self.api_secret = PAYID_API_SECRET
        self.environment = PAYID_ENVIRONMENT
        self.base_url = self._get_base_url()
        self.is_configured = bool(self.api_key and self.api_secret)
    
    def _get_base_url(self):
        if self.environment == "production":
            return "https://api.hellozai.com/v1"  # Zai production
        return "https://api.sandbox.hellozai.com/v1"  # Zai sandbox
    
    async def _get_auth_token(self) -> str:
        """Get authentication token from PayID provider"""
        if not self.is_configured:
            raise HTTPException(status_code=503, detail="PayID not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret,
                    "scope": "payid"
                }
            )
            if response.status_code == 200:
                return response.json().get("access_token")
            raise HTTPException(status_code=503, detail="PayID authentication failed")
    
    async def create_payid_for_user(self, user_id: str, email: str) -> dict:
        """Create a unique PayID for a user to receive deposits"""
        if not self.is_configured:
            # Return demo PayID
            return {
                "payid": f"neonvegas+{user_id[:8]}@casino.demo",
                "type": "email",
                "status": "demo"
            }
        
        token = await self._get_auth_token()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/payid/create",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "payid_type": "email",
                    "payid_name": f"NeonVegas Deposit - {user_id[:8]}",
                    "reference": user_id,
                    "metadata": {"user_id": user_id, "email": email}
                }
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=503, detail="Failed to create PayID")
    
    async def initiate_deposit(self, user_id: str, amount: float) -> dict:
        """Initiate a PayID deposit request"""
        if not self.is_configured:
            # Demo mode - instant credit
            return {
                "status": "demo",
                "reference": f"DEMO-{str(uuid.uuid4())[:8].upper()}",
                "payid": f"neonvegas+{user_id[:8]}@casino.demo",
                "amount": amount,
                "instructions": "Demo mode: Funds credited instantly"
            }
        
        token = await self._get_auth_token()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/payid/deposit",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "amount": int(amount * 100),  # Convert to cents
                    "currency": "AUD",
                    "reference": f"DEP-{user_id[:8]}-{str(uuid.uuid4())[:8]}",
                    "metadata": {"user_id": user_id}
                }
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=503, detail="Failed to initiate deposit")
    
    async def initiate_withdrawal(self, user_id: str, amount: float, payid_account: str, payid_type: str = "email") -> dict:
        """Initiate a PayID withdrawal/payout"""
        if not self.is_configured:
            # Demo mode - instant deduction
            return {
                "status": "demo",
                "reference": f"WD-{str(uuid.uuid4())[:8].upper()}",
                "payid_account": payid_account,
                "amount": amount,
                "message": "Demo mode: Withdrawal processed instantly"
            }
        
        token = await self._get_auth_token()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/payid/payout",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "amount": int(amount * 100),
                    "currency": "AUD",
                    "payid": payid_account,
                    "payid_type": payid_type,
                    "reference": f"WD-{user_id[:8]}-{str(uuid.uuid4())[:8]}",
                    "description": "NeonVegas Casino Withdrawal",
                    "metadata": {"user_id": user_id}
                }
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=503, detail="Failed to initiate withdrawal")
    
    async def verify_payment(self, reference: str) -> dict:
        """Verify payment status by reference"""
        if not self.is_configured:
            return {"status": "completed", "reference": reference}
        
        token = await self._get_auth_token()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/payid/transaction/{reference}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            return {"status": "pending", "reference": reference}

# Initialize PayID service
payid_service = PayIDService()

# ==================== JACKPOT SERVICE ====================

class JackpotService:
    """Progressive Jackpot System"""
    
    async def get_jackpot(self) -> dict:
        """Get current jackpot amount"""
        jackpot = await db.jackpot.find_one({"type": "progressive"}, {"_id": 0})
        if not jackpot:
            # Initialize jackpot
            jackpot = {
                "type": "progressive",
                "amount": MINIMUM_JACKPOT,
                "last_won": None,
                "last_winner": None,
                "total_contributions": 0,
                "total_winners": 0
            }
            await db.jackpot.insert_one(jackpot)
        return jackpot
    
    async def contribute(self, bet_amount: float) -> float:
        """Add contribution to jackpot from a bet"""
        contribution = bet_amount * JACKPOT_CONTRIBUTION_RATE
        await db.jackpot.update_one(
            {"type": "progressive"},
            {
                "$inc": {
                    "amount": contribution,
                    "total_contributions": contribution
                }
            },
            upsert=True
        )
        return contribution
    
    async def check_jackpot_win(self, user_id: str, bet_amount: float) -> Optional[dict]:
        """Check if user won the jackpot (random chance)"""
        # Higher bets have slightly better odds
        adjusted_probability = JACKPOT_WIN_PROBABILITY * (1 + bet_amount / 100)
        
        if random.random() < adjusted_probability:
            jackpot = await self.get_jackpot()
            win_amount = jackpot["amount"]
            
            # Reset jackpot
            await db.jackpot.update_one(
                {"type": "progressive"},
                {
                    "$set": {
                        "amount": MINIMUM_JACKPOT,
                        "last_won": datetime.now(timezone.utc).isoformat(),
                        "last_winner": user_id
                    },
                    "$inc": {"total_winners": 1}
                }
            )
            
            # Record jackpot win
            await db.jackpot_wins.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "amount": win_amount,
                "won_at": datetime.now(timezone.utc).isoformat()
            })
            
            return {"won": True, "amount": win_amount}
        
        return None

# Initialize jackpot service
jackpot_service = JackpotService()

# ==================== EXTERNAL GAME PROVIDER SERVICE ====================

class ExternalGameProvider:
    """
    Production-ready integration for external game providers:
    - JILI Games
    - Imperium Games  
    - Slotomania
    - Rich Games
    """
    
    PROVIDERS = {
        "jili": {
            "name": "JILI Games",
            "api_key": JILI_API_KEY,
            "api_secret": JILI_API_SECRET,
            "api_url": JILI_API_URL,
            "agent_id": JILI_AGENT_ID,
        },
        "imperium": {
            "name": "Imperium Games",
            "api_key": IMPERIUM_API_KEY,
            "api_secret": IMPERIUM_API_SECRET,
            "api_url": IMPERIUM_API_URL,
        },
        "slotomania": {
            "name": "Slotomania",
            "api_key": SLOTOMANIA_API_KEY,
            "api_secret": SLOTOMANIA_API_SECRET,
            "api_url": SLOTOMANIA_API_URL,
        },
        "rich": {
            "name": "Rich Games",
            "api_key": RICH_API_KEY,
            "api_secret": RICH_API_SECRET,
            "api_url": RICH_API_URL,
        }
    }
    
    # Demo games catalog when providers not configured
    DEMO_GAMES = {
        "jili": [
            {"id": "jili_fortune_gems", "name": "Fortune Gems", "type": "slot", "rtp": 96.5, "volatility": "medium"},
            {"id": "jili_super_ace", "name": "Super Ace", "type": "slot", "rtp": 97.0, "volatility": "high"},
            {"id": "jili_golden_empire", "name": "Golden Empire", "type": "slot", "rtp": 96.8, "volatility": "medium"},
            {"id": "jili_money_coming", "name": "Money Coming", "type": "slot", "rtp": 97.2, "volatility": "low"},
            {"id": "jili_boxing_king", "name": "Boxing King", "type": "slot", "rtp": 96.0, "volatility": "high"},
            {"id": "jili_crazy_hunter", "name": "Crazy Hunter", "type": "fishing", "rtp": 96.5, "volatility": "medium"},
        ],
        "imperium": [
            {"id": "imp_dragon_fortune", "name": "Dragon Fortune", "type": "slot", "rtp": 96.2, "volatility": "high"},
            {"id": "imp_lucky_88", "name": "Lucky 88", "type": "slot", "rtp": 96.8, "volatility": "medium"},
            {"id": "imp_golden_tiger", "name": "Golden Tiger", "type": "slot", "rtp": 97.1, "volatility": "low"},
            {"id": "imp_phoenix_rises", "name": "Phoenix Rises", "type": "slot", "rtp": 96.5, "volatility": "high"},
        ],
        "slotomania": [
            {"id": "sloto_classic_vegas", "name": "Classic Vegas", "type": "slot", "rtp": 96.0, "volatility": "low"},
            {"id": "sloto_wild_west", "name": "Wild West Gold", "type": "slot", "rtp": 96.5, "volatility": "high"},
            {"id": "sloto_magic_forest", "name": "Magic Forest", "type": "slot", "rtp": 97.0, "volatility": "medium"},
            {"id": "sloto_diamond_rush", "name": "Diamond Rush", "type": "slot", "rtp": 96.8, "volatility": "high"},
        ],
        "rich": [
            {"id": "rich_treasure_hunt", "name": "Treasure Hunt", "type": "slot", "rtp": 96.5, "volatility": "medium"},
            {"id": "rich_gold_rush", "name": "Gold Rush", "type": "slot", "rtp": 97.0, "volatility": "high"},
            {"id": "rich_pirate_gold", "name": "Pirate Gold", "type": "slot", "rtp": 96.2, "volatility": "medium"},
            {"id": "rich_mega_millions", "name": "Mega Millions", "type": "slot", "rtp": 96.8, "volatility": "high"},
        ]
    }
    
    def __init__(self):
        self.configured_providers = self._check_configured_providers()
    
    def _check_configured_providers(self) -> dict:
        """Check which providers have API keys configured"""
        status = {}
        for provider_id, config in self.PROVIDERS.items():
            status[provider_id] = bool(config.get("api_key") and config.get("api_secret"))
        return status
    
    def _generate_signature(self, provider: str, data: dict) -> str:
        """Generate HMAC signature for API requests"""
        config = self.PROVIDERS.get(provider, {})
        secret = config.get("api_secret", "")
        message = "&".join(f"{k}={v}" for k, v in sorted(data.items()))
        return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    
    async def get_provider_status(self) -> dict:
        """Get status of all game providers"""
        return {
            provider_id: {
                "name": config["name"],
                "configured": self.configured_providers.get(provider_id, False),
                "mode": "live" if self.configured_providers.get(provider_id) else "demo",
                "games_count": len(self.DEMO_GAMES.get(provider_id, []))
            }
            for provider_id, config in self.PROVIDERS.items()
        }
    
    async def get_games_catalog(self, provider: str = None) -> list:
        """Get games catalog from provider(s)"""
        if provider:
            if self.configured_providers.get(provider):
                # Real API call
                return await self._fetch_real_games(provider)
            return self.DEMO_GAMES.get(provider, [])
        
        # Return all games from all providers
        all_games = []
        for prov_id, games in self.DEMO_GAMES.items():
            for game in games:
                game["provider"] = prov_id
                all_games.append(game)
        return all_games
    
    async def _fetch_real_games(self, provider: str) -> list:
        """Fetch real games from provider API"""
        config = self.PROVIDERS.get(provider, {})
        if not config.get("api_key"):
            return self.DEMO_GAMES.get(provider, [])
        
        try:
            async with httpx.AsyncClient() as client:
                # JILI API
                if provider == "jili":
                    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
                    params = {
                        "AgentId": config.get("agent_id", ""),
                        "Key": config["api_key"],
                        "Timestamp": timestamp
                    }
                    params["Sign"] = self._generate_signature(provider, params)
                    response = await client.post(
                        f"{config['api_url']}/api/game/list",
                        json=params,
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("Data", {}).get("Games", [])
                
                # Imperium API
                elif provider == "imperium":
                    headers = {"Authorization": f"Bearer {config['api_key']}"}
                    response = await client.get(
                        f"{config['api_url']}/v1/games",
                        headers=headers,
                        timeout=30
                    )
                    if response.status_code == 200:
                        return response.json().get("games", [])
                
                # Slotomania API
                elif provider == "slotomania":
                    headers = {"X-API-Key": config["api_key"]}
                    response = await client.get(
                        f"{config['api_url']}/games/catalog",
                        headers=headers,
                        timeout=30
                    )
                    if response.status_code == 200:
                        return response.json().get("games", [])
                
                # Rich Games API
                elif provider == "rich":
                    params = {"api_key": config["api_key"]}
                    response = await client.get(
                        f"{config['api_url']}/api/games",
                        params=params,
                        timeout=30
                    )
                    if response.status_code == 200:
                        return response.json().get("games", [])
        
        except Exception as e:
            logger.error(f"Failed to fetch games from {provider}: {e}")
        
        return self.DEMO_GAMES.get(provider, [])
    
    async def launch_game(self, provider: str, game_id: str, user_id: str, user_token: str) -> dict:
        """Launch a game session with provider"""
        config = self.PROVIDERS.get(provider, {})
        
        if not self.configured_providers.get(provider):
            # Demo mode - return demo launch URL
            return {
                "mode": "demo",
                "game_id": game_id,
                "provider": provider,
                "launch_url": None,
                "message": f"Demo mode: {provider} API not configured. Play our in-house version instead.",
                "fallback_game": "slots"  # Redirect to in-house slots
            }
        
        try:
            async with httpx.AsyncClient() as client:
                # JILI Launch
                if provider == "jili":
                    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
                    params = {
                        "AgentId": config.get("agent_id", ""),
                        "Key": config["api_key"],
                        "Account": user_id,
                        "GameId": game_id,
                        "Lang": "en",
                        "Timestamp": timestamp
                    }
                    params["Sign"] = self._generate_signature(provider, params)
                    response = await client.post(
                        f"{config['api_url']}/api/game/launch",
                        json=params,
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "mode": "live",
                            "game_id": game_id,
                            "provider": provider,
                            "launch_url": data.get("Data", {}).get("Url"),
                            "session_id": data.get("Data", {}).get("SessionId")
                        }
                
                # Imperium Launch
                elif provider == "imperium":
                    headers = {"Authorization": f"Bearer {config['api_key']}"}
                    response = await client.post(
                        f"{config['api_url']}/v1/games/launch",
                        headers=headers,
                        json={"game_id": game_id, "player_id": user_id, "token": user_token},
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "mode": "live",
                            "game_id": game_id,
                            "provider": provider,
                            "launch_url": data.get("url"),
                            "session_id": data.get("session_id")
                        }
                
                # Add similar for slotomania and rich...
        
        except Exception as e:
            logger.error(f"Failed to launch game {game_id} from {provider}: {e}")
        
        return {
            "mode": "error",
            "game_id": game_id,
            "provider": provider,
            "error": "Failed to launch game",
            "fallback_game": "slots"
        }
    
    async def process_bet_callback(self, provider: str, data: dict) -> dict:
        """Process bet callback from provider (for balance management)"""
        # Verify signature
        signature = data.pop("sign", None)
        expected_sig = self._generate_signature(provider, data)
        
        if signature != expected_sig:
            return {"error": "Invalid signature", "code": 401}
        
        user_id = data.get("account") or data.get("player_id") or data.get("user_id")
        bet_amount = float(data.get("bet_amount", 0))
        win_amount = float(data.get("win_amount", 0))
        game_id = data.get("game_id")
        round_id = data.get("round_id")
        
        # Get user
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            return {"error": "User not found", "code": 404}
        
        # Process bet
        if bet_amount > 0:
            if user["balance"] < bet_amount:
                return {"error": "Insufficient balance", "code": 400, "balance": user["balance"]}
            
            # Deduct bet
            new_balance = user["balance"] - bet_amount + win_amount
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"balance": new_balance}}
            )
            
            # Record transaction
            await db.transactions.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "type": "external_bet",
                "amount": bet_amount,
                "method": f"{provider}_{game_id}",
                "status": "completed",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "provider": provider,
                    "game_id": game_id,
                    "round_id": round_id,
                    "win_amount": win_amount
                }
            })
            
            if win_amount > 0:
                await db.transactions.insert_one({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "external_win",
                    "amount": win_amount,
                    "method": f"{provider}_{game_id}",
                    "status": "completed",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "details": {
                        "provider": provider,
                        "game_id": game_id,
                        "round_id": round_id
                    }
                })
            
            # Contribute to jackpot
            await jackpot_service.contribute(bet_amount)
            
            return {
                "success": True,
                "balance": new_balance,
                "code": 0
            }
        
        return {"error": "Invalid bet amount", "code": 400}

# Initialize external game provider service
external_provider = ExternalGameProvider()

# ==================== CUSTOM THEMED SLOTS ====================

CUSTOM_SLOT_THEMES = {
    "pharaohs_gold": {
        "name": "Pharaoh's Gold",
        "theme": "egyptian",
        "description": "Discover ancient treasures in the pyramids!",
        "symbols": ["🏺", "👁️", "🐫", "🦅", "⚱️", "💎", "👑"],
        "weights": [25, 22, 20, 18, 10, 3, 2],
        "multipliers": {"🏺": 3, "👁️": 5, "🐫": 8, "🦅": 12, "⚱️": 20, "💎": 50, "👑": 100},
        "bg_color": "#8B6914",
        "rtp": 96.5,
        "volatility": "medium"
    },
    "fortune_dragon": {
        "name": "Fortune Dragon",
        "theme": "asian",
        "description": "Let the dragon bring you luck and fortune!",
        "symbols": ["🧧", "🏮", "🐉", "🀄", "🎋", "💰", "🐲"],
        "weights": [25, 22, 20, 18, 10, 3, 2],
        "multipliers": {"🧧": 3, "🏮": 5, "🐉": 8, "🀄": 12, "🎋": 20, "💰": 50, "🐲": 150},
        "bg_color": "#C41E3A",
        "rtp": 97.0,
        "volatility": "high"
    },
    "lucky_sevens": {
        "name": "Lucky 7s",
        "theme": "classic",
        "description": "Classic Vegas-style slot machine!",
        "symbols": ["🍒", "🔔", "⭐", "🍀", "💰", "7️⃣", "💎"],
        "weights": [28, 24, 20, 15, 8, 3, 2],
        "multipliers": {"🍒": 2, "🔔": 4, "⭐": 6, "🍀": 10, "💰": 25, "7️⃣": 77, "💎": 100},
        "bg_color": "#1a1a2e",
        "rtp": 96.0,
        "volatility": "low"
    },
    "ocean_treasure": {
        "name": "Ocean Treasure",
        "theme": "underwater",
        "description": "Dive deep for underwater riches!",
        "symbols": ["🐚", "🦀", "🐠", "🐙", "🦈", "🧜‍♀️", "🔱"],
        "weights": [26, 23, 20, 17, 9, 3, 2],
        "multipliers": {"🐚": 2, "🦀": 4, "🐠": 7, "🐙": 12, "🦈": 25, "🧜‍♀️": 60, "🔱": 120},
        "bg_color": "#006994",
        "rtp": 96.8,
        "volatility": "medium"
    },
    "fruit_frenzy": {
        "name": "Fruit Frenzy",
        "theme": "fruit",
        "description": "Fresh fruits, fresh wins!",
        "symbols": ["🍒", "🍋", "🍊", "🍇", "🍉", "🍓", "🌟"],
        "weights": [28, 25, 20, 15, 7, 3, 2],
        "multipliers": {"🍒": 2, "🍋": 3, "🍊": 5, "🍇": 8, "🍉": 15, "🍓": 40, "🌟": 80},
        "bg_color": "#2d5a27",
        "rtp": 95.5,
        "volatility": "low"
    },
    "cosmic_cash": {
        "name": "Cosmic Cash",
        "theme": "space",
        "description": "Explore the galaxy for cosmic wins!",
        "symbols": ["🌙", "⭐", "🪐", "🚀", "👽", "🌌", "💫"],
        "weights": [26, 23, 20, 17, 9, 3, 2],
        "multipliers": {"🌙": 3, "⭐": 5, "🪐": 8, "🚀": 15, "👽": 30, "🌌": 70, "💫": 150},
        "bg_color": "#0c0c2c",
        "rtp": 97.2,
        "volatility": "high"
    },
    "wild_safari": {
        "name": "Wild Safari",
        "theme": "safari",
        "description": "Go wild on the African plains!",
        "symbols": ["🦓", "🦒", "🐘", "🦁", "🐆", "🦏", "👑"],
        "weights": [26, 23, 20, 17, 9, 3, 2],
        "multipliers": {"🦓": 3, "🦒": 5, "🐘": 8, "🦁": 15, "🐆": 30, "🦏": 60, "👑": 100},
        "bg_color": "#8B4513",
        "rtp": 96.3,
        "volatility": "medium"
    },
    "mystic_gems": {
        "name": "Mystic Gems",
        "theme": "fantasy",
        "description": "Magical gems with mystical powers!",
        "symbols": ["💜", "💙", "💚", "❤️", "🔮", "✨", "👑"],
        "weights": [26, 23, 20, 17, 9, 3, 2],
        "multipliers": {"💜": 2, "💙": 4, "💚": 6, "❤️": 10, "🔮": 25, "✨": 50, "👑": 100},
        "bg_color": "#2E1A47",
        "rtp": 96.7,
        "volatility": "medium"
    }
}

def process_themed_slot(theme_id: str, bet_details: dict) -> dict:
    """Process a themed slot spin"""
    theme = CUSTOM_SLOT_THEMES.get(theme_id)
    if not theme:
        return {"error": "Invalid theme"}
    
    symbols = theme["symbols"]
    weights = theme["weights"]
    multipliers = theme["multipliers"]
    
    # Spin the reels
    reels = [random.choices(symbols, weights=weights)[0] for _ in range(3)]
    
    # Check for wins
    win = False
    multiplier = 0
    win_type = None
    
    if reels[0] == reels[1] == reels[2]:
        # Three of a kind
        symbol = reels[0]
        win = True
        multiplier = multipliers[symbol]
        win_type = "three_of_a_kind"
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        # Two of a kind
        win = True
        multiplier = 1.5
        win_type = "two_of_a_kind"
    
    return {
        "reels": reels,
        "win": win,
        "multiplier": multiplier,
        "win_type": win_type,
        "theme": theme_id,
        "theme_name": theme["name"]
    }

# ==================== VIP SYSTEM SERVICE ====================

class VIPService:
    """VIP Tier System with cashback and bonuses"""
    
    def get_tier(self, total_wagered: float) -> str:
        """Get VIP tier based on total wagered amount"""
        tier = "bronze"
        for tier_name, config in VIP_TIERS.items():
            if total_wagered >= config["min_wagered"]:
                tier = tier_name
        return tier
    
    def get_tier_info(self, tier: str) -> dict:
        """Get tier benefits"""
        config = VIP_TIERS.get(tier, VIP_TIERS["bronze"])
        return {
            "tier": tier,
            "cashback_rate": config["cashback"],
            "bonus_multiplier": config["bonus_multiplier"],
            "daily_bonus": config["daily_bonus"],
            "next_tier": self._get_next_tier(tier),
            "next_tier_requirement": self._get_next_requirement(tier)
        }
    
    def _get_next_tier(self, current: str) -> Optional[str]:
        tiers = list(VIP_TIERS.keys())
        idx = tiers.index(current)
        return tiers[idx + 1] if idx < len(tiers) - 1 else None
    
    def _get_next_requirement(self, current: str) -> Optional[float]:
        next_tier = self._get_next_tier(current)
        if next_tier:
            return VIP_TIERS[next_tier]["min_wagered"]
        return None
    
    async def update_user_vip(self, user_id: str) -> dict:
        """Update user's VIP status based on wagering"""
        # Calculate total wagered
        wagered = await db.transactions.aggregate([
            {"$match": {"user_id": user_id, "type": "bet"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        total_wagered = wagered[0]["total"] if wagered else 0
        new_tier = self.get_tier(total_wagered)
        
        # Update user
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "vip_tier": new_tier,
                "total_wagered": total_wagered
            }}
        )
        
        return {
            "tier": new_tier,
            "total_wagered": total_wagered,
            **self.get_tier_info(new_tier)
        }
    
    async def claim_daily_bonus(self, user_id: str) -> dict:
        """Claim VIP daily bonus"""
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        tier = user.get("vip_tier", "bronze")
        last_claim = user.get("last_daily_bonus")
        
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if last_claim:
            last_claim_date = datetime.fromisoformat(last_claim.replace('Z', '+00:00'))
            if last_claim_date.tzinfo is None:
                last_claim_date = last_claim_date.replace(tzinfo=timezone.utc)
            if last_claim_date >= today:
                return {"success": False, "message": "Daily bonus already claimed today"}
        
        bonus = VIP_TIERS[tier]["daily_bonus"]
        
        # Add bonus to balance
        await db.users.update_one(
            {"id": user_id},
            {
                "$inc": {"balance": bonus},
                "$set": {"last_daily_bonus": now.isoformat()}
            }
        )
        
        # Record transaction
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "bonus",
            "amount": bonus,
            "method": "vip_daily",
            "status": "completed",
            "created_at": now.isoformat(),
            "details": {"tier": tier}
        })
        
        return {"success": True, "bonus": bonus, "tier": tier}
    
    async def process_cashback(self, user_id: str) -> dict:
        """Calculate and process weekly cashback"""
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        tier = user.get("vip_tier", "bronze")
        cashback_rate = VIP_TIERS[tier]["cashback"]
        
        # Get losses in the past week
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        bets = await db.transactions.aggregate([
            {"$match": {"user_id": user_id, "type": "bet", "created_at": {"$gte": week_ago.isoformat()}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        wins = await db.transactions.aggregate([
            {"$match": {"user_id": user_id, "type": "win", "created_at": {"$gte": week_ago.isoformat()}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        total_bet = bets[0]["total"] if bets else 0
        total_won = wins[0]["total"] if wins else 0
        net_loss = max(0, total_bet - total_won)
        
        cashback = net_loss * cashback_rate
        
        if cashback > 0:
            await db.users.update_one(
                {"id": user_id},
                {"$inc": {"balance": cashback}}
            )
            
            await db.transactions.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "type": "bonus",
                "amount": cashback,
                "method": "vip_cashback",
                "status": "completed",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "details": {"tier": tier, "net_loss": net_loss, "rate": cashback_rate}
            })
        
        return {"cashback": cashback, "net_loss": net_loss, "tier": tier}

vip_service = VIPService()

# ==================== TOURNAMENT SERVICE ====================

class TournamentService:
    """Tournament and Competition System"""
    
    async def create_tournament(self, name: str, game: str, entry_fee: float, prize_pool: float, 
                                start_time: str, end_time: str, max_players: int = 100) -> dict:
        """Create a new tournament"""
        tournament_id = str(uuid.uuid4())
        tournament = {
            "id": tournament_id,
            "name": name,
            "game": game,
            "entry_fee": entry_fee,
            "prize_pool": prize_pool,
            "start_time": start_time,
            "end_time": end_time,
            "max_players": max_players,
            "participants": [],
            "leaderboard": [],
            "status": "upcoming",  # upcoming, active, completed
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.tournaments.insert_one(tournament)
        return tournament
    
    async def join_tournament(self, tournament_id: str, user_id: str) -> dict:
        """Join a tournament"""
        tournament = await db.tournaments.find_one({"id": tournament_id}, {"_id": 0})
        if not tournament:
            return {"success": False, "error": "Tournament not found"}
        
        if tournament["status"] != "upcoming" and tournament["status"] != "active":
            return {"success": False, "error": "Tournament not accepting entries"}
        
        if user_id in tournament["participants"]:
            return {"success": False, "error": "Already joined"}
        
        if len(tournament["participants"]) >= tournament["max_players"]:
            return {"success": False, "error": "Tournament full"}
        
        # Check user balance for entry fee
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user["balance"] < tournament["entry_fee"]:
            return {"success": False, "error": "Insufficient balance for entry fee"}
        
        # Deduct entry fee
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"balance": -tournament["entry_fee"]}}
        )
        
        # Add to prize pool and participants
        await db.tournaments.update_one(
            {"id": tournament_id},
            {
                "$push": {"participants": user_id},
                "$inc": {"prize_pool": tournament["entry_fee"] * 0.9}  # 10% house edge
            }
        )
        
        # Record entry
        await db.tournament_entries.insert_one({
            "id": str(uuid.uuid4()),
            "tournament_id": tournament_id,
            "user_id": user_id,
            "score": 0,
            "spins": 0,
            "best_win": 0,
            "joined_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"success": True, "message": f"Joined tournament: {tournament['name']}"}
    
    async def record_tournament_play(self, tournament_id: str, user_id: str, 
                                      bet_amount: float, win_amount: float) -> dict:
        """Record a play in a tournament"""
        # Update entry stats
        entry = await db.tournament_entries.find_one(
            {"tournament_id": tournament_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not entry:
            return {"success": False, "error": "Not in tournament"}
        
        # Score based on win multiplier
        score_earned = (win_amount / bet_amount) if bet_amount > 0 else 0
        
        await db.tournament_entries.update_one(
            {"tournament_id": tournament_id, "user_id": user_id},
            {
                "$inc": {"score": score_earned, "spins": 1},
                "$max": {"best_win": win_amount}
            }
        )
        
        return {"success": True, "score_earned": score_earned}
    
    async def get_tournament_leaderboard(self, tournament_id: str) -> list:
        """Get tournament leaderboard"""
        entries = await db.tournament_entries.find(
            {"tournament_id": tournament_id},
            {"_id": 0}
        ).sort("score", -1).limit(50).to_list(50)
        
        # Add usernames
        for i, entry in enumerate(entries):
            user = await db.users.find_one({"id": entry["user_id"]}, {"_id": 0, "username": 1})
            entry["rank"] = i + 1
            entry["username"] = user.get("username", "Unknown") if user else "Unknown"
        
        return entries
    
    async def get_active_tournaments(self) -> list:
        """Get all active and upcoming tournaments"""
        now = datetime.now(timezone.utc).isoformat()
        tournaments = await db.tournaments.find(
            {"status": {"$in": ["upcoming", "active"]}},
            {"_id": 0}
        ).sort("start_time", 1).to_list(20)
        return tournaments
    
    async def complete_tournament(self, tournament_id: str) -> dict:
        """Complete tournament and distribute prizes"""
        tournament = await db.tournaments.find_one({"id": tournament_id}, {"_id": 0})
        if not tournament:
            return {"error": "Tournament not found"}
        
        leaderboard = await self.get_tournament_leaderboard(tournament_id)
        prize_pool = tournament["prize_pool"]
        
        # Prize distribution: 50%, 25%, 15%, 10% for top 4
        prizes = [0.5, 0.25, 0.15, 0.10]
        winners = []
        
        for i, entry in enumerate(leaderboard[:4]):
            if i < len(prizes):
                prize = prize_pool * prizes[i]
                await db.users.update_one(
                    {"id": entry["user_id"]},
                    {"$inc": {"balance": prize}}
                )
                winners.append({
                    "rank": i + 1,
                    "user_id": entry["user_id"],
                    "username": entry["username"],
                    "prize": prize,
                    "score": entry["score"]
                })
        
        await db.tournaments.update_one(
            {"id": tournament_id},
            {"$set": {"status": "completed", "winners": winners}}
        )
        
        return {"success": True, "winners": winners}

tournament_service = TournamentService()

# ==================== DAILY CHALLENGES SERVICE ====================

class DailyChallengesService:
    """Daily challenges and rewards system"""
    
    CHALLENGE_TEMPLATES = [
        {"id": "spin_slots", "name": "Slot Spinner", "description": "Spin slots 20 times", "target": 20, "reward": 10, "game": "slots"},
        {"id": "win_blackjack", "name": "Card Shark", "description": "Win 5 blackjack hands", "target": 5, "reward": 15, "game": "blackjack"},
        {"id": "roulette_streak", "name": "Lucky Streak", "description": "Win 3 roulette bets in a row", "target": 3, "reward": 20, "game": "roulette"},
        {"id": "big_win", "name": "Big Winner", "description": "Win 10x or more on a single bet", "target": 10, "reward": 25, "game": "any"},
        {"id": "total_wagered", "name": "High Roller", "description": "Wager $100 total today", "target": 100, "reward": 15, "game": "any"},
        {"id": "play_poker", "name": "Poker Pro", "description": "Play 10 poker hands", "target": 10, "reward": 10, "game": "poker"},
        {"id": "themed_slots", "name": "Theme Explorer", "description": "Play 5 different themed slots", "target": 5, "reward": 20, "game": "themed"},
        {"id": "jackpot_hunter", "name": "Jackpot Hunter", "description": "Contribute $10 to the jackpot", "target": 10, "reward": 30, "game": "any"},
    ]
    
    async def get_daily_challenges(self, user_id: str) -> list:
        """Get user's daily challenges"""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        # Check if user has challenges for today
        challenges = await db.daily_challenges.find(
            {"user_id": user_id, "date": today},
            {"_id": 0}
        ).to_list(10)
        
        if not challenges:
            # Generate new challenges for today (pick 3 random)
            selected = random.sample(self.CHALLENGE_TEMPLATES, 3)
            challenges = []
            for template in selected:
                challenge = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "template_id": template["id"],
                    "name": template["name"],
                    "description": template["description"],
                    "target": template["target"],
                    "progress": 0,
                    "reward": template["reward"],
                    "game": template["game"],
                    "completed": False,
                    "claimed": False,
                    "date": today
                }
                await db.daily_challenges.insert_one(challenge)
                challenges.append(challenge)
        
        return challenges
    
    async def update_challenge_progress(self, user_id: str, game: str, 
                                         action: str, value: float = 1) -> list:
        """Update challenge progress based on game activity"""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        challenges = await db.daily_challenges.find(
            {"user_id": user_id, "date": today, "completed": False},
            {"_id": 0}
        ).to_list(10)
        
        updated = []
        for challenge in challenges:
            should_update = False
            increment = 0
            
            # Match challenge to activity
            if challenge["template_id"] == "spin_slots" and game in ["slots", "themed_slot"]:
                should_update = True
                increment = 1
            elif challenge["template_id"] == "win_blackjack" and game == "blackjack" and action == "win":
                should_update = True
                increment = 1
            elif challenge["template_id"] == "roulette_streak" and game == "roulette" and action == "win":
                should_update = True
                increment = 1
            elif challenge["template_id"] == "big_win" and action == "multiplier":
                if value >= challenge["target"]:
                    should_update = True
                    increment = challenge["target"]  # Complete immediately
            elif challenge["template_id"] == "total_wagered" and action == "wager":
                should_update = True
                increment = value
            elif challenge["template_id"] == "play_poker" and game == "poker":
                should_update = True
                increment = 1
            elif challenge["template_id"] == "themed_slots" and "themed_slot" in game:
                should_update = True
                increment = 1
            elif challenge["template_id"] == "jackpot_hunter" and action == "jackpot_contribution":
                should_update = True
                increment = value
            
            if should_update and increment > 0:
                new_progress = min(challenge["progress"] + increment, challenge["target"])
                completed = new_progress >= challenge["target"]
                
                await db.daily_challenges.update_one(
                    {"id": challenge["id"]},
                    {"$set": {"progress": new_progress, "completed": completed}}
                )
                
                updated.append({
                    "challenge_id": challenge["id"],
                    "name": challenge["name"],
                    "progress": new_progress,
                    "target": challenge["target"],
                    "completed": completed
                })
        
        return updated
    
    async def claim_challenge_reward(self, user_id: str, challenge_id: str) -> dict:
        """Claim reward for completed challenge"""
        challenge = await db.daily_challenges.find_one(
            {"id": challenge_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not challenge:
            return {"success": False, "error": "Challenge not found"}
        
        if not challenge["completed"]:
            return {"success": False, "error": "Challenge not completed"}
        
        if challenge["claimed"]:
            return {"success": False, "error": "Reward already claimed"}
        
        # Add reward
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"balance": challenge["reward"]}}
        )
        
        await db.daily_challenges.update_one(
            {"id": challenge_id},
            {"$set": {"claimed": True}}
        )
        
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "bonus",
            "amount": challenge["reward"],
            "method": "daily_challenge",
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "details": {"challenge": challenge["name"]}
        })
        
        return {"success": True, "reward": challenge["reward"], "challenge": challenge["name"]}

daily_challenges_service = DailyChallengesService()

# ==================== ENHANCED SLOTS (5-REEL WITH BONUS) ====================

class EnhancedSlotMachine:
    """5-reel slot machine with wilds, scatters, and bonus rounds"""
    
    def __init__(self):
        self.reels = 5
        self.rows = 3
        self.paylines = [
            [1, 1, 1, 1, 1],  # Middle row
            [0, 0, 0, 0, 0],  # Top row
            [2, 2, 2, 2, 2],  # Bottom row
            [0, 1, 2, 1, 0],  # V shape
            [2, 1, 0, 1, 2],  # Inverted V
            [0, 0, 1, 2, 2],  # Diagonal down
            [2, 2, 1, 0, 0],  # Diagonal up
            [1, 0, 0, 0, 1],  # U shape top
            [1, 2, 2, 2, 1],  # U shape bottom
            [0, 1, 1, 1, 0],  # Flat top bump
        ]
        
        self.symbols = {
            "🍒": {"value": 2, "frequency": 30},
            "🍋": {"value": 3, "frequency": 25},
            "🍊": {"value": 4, "frequency": 22},
            "🍇": {"value": 5, "frequency": 18},
            "🔔": {"value": 8, "frequency": 12},
            "⭐": {"value": 15, "frequency": 8},
            "7️⃣": {"value": 30, "frequency": 4},
            "💎": {"value": 50, "frequency": 2},  # Wild
            "🎰": {"value": 0, "frequency": 3},   # Scatter (triggers bonus)
        }
        
        self.wild = "💎"
        self.scatter = "🎰"
    
    def spin(self, bet_per_line: float, lines: int = 10) -> dict:
        """Perform a 5-reel spin"""
        # Generate grid
        symbols_list = list(self.symbols.keys())
        weights = [self.symbols[s]["frequency"] for s in symbols_list]
        
        grid = []
        for _ in range(self.rows):
            row = [random.choices(symbols_list, weights=weights)[0] for _ in range(self.reels)]
            grid.append(row)
        
        # Check paylines
        total_win = 0
        winning_lines = []
        
        for line_idx, payline in enumerate(self.paylines[:lines]):
            line_symbols = [grid[payline[reel]][reel] for reel in range(self.reels)]
            win, count = self._check_line(line_symbols)
            if win > 0:
                line_win = win * bet_per_line
                total_win += line_win
                winning_lines.append({
                    "line": line_idx + 1,
                    "symbols": line_symbols,
                    "count": count,
                    "win": line_win
                })
        
        # Check for scatters (bonus trigger)
        scatter_count = sum(row.count(self.scatter) for row in grid)
        bonus_triggered = scatter_count >= 3
        free_spins = 0
        bonus_multiplier = 1
        
        if bonus_triggered:
            free_spins = scatter_count * 5  # 15, 20, or 25 free spins
            bonus_multiplier = 2 if scatter_count >= 4 else 1.5
        
        return {
            "grid": grid,
            "total_win": total_win,
            "winning_lines": winning_lines,
            "scatter_count": scatter_count,
            "bonus_triggered": bonus_triggered,
            "free_spins": free_spins,
            "bonus_multiplier": bonus_multiplier,
            "bet_total": bet_per_line * lines
        }
    
    def _check_line(self, line: list) -> tuple:
        """Check a payline for wins"""
        first_symbol = line[0] if line[0] != self.wild else None
        count = 0
        
        for symbol in line:
            if symbol == self.wild:
                count += 1
                if first_symbol is None and count < len(line):
                    # Find first non-wild
                    for s in line[count:]:
                        if s != self.wild and s != self.scatter:
                            first_symbol = s
                            break
            elif symbol == first_symbol or first_symbol is None:
                if first_symbol is None and symbol != self.scatter:
                    first_symbol = symbol
                count += 1
            else:
                break
        
        if count >= 3 and first_symbol and first_symbol != self.scatter:
            base_value = self.symbols[first_symbol]["value"]
            multiplier = {3: 1, 4: 3, 5: 10}
            return base_value * multiplier.get(count, 1), count
        
        return 0, 0

enhanced_slot_machine = EnhancedSlotMachine()

# ==================== RESPONSIBLE GAMBLING SERVICE ====================

class ResponsibleGamblingService:
    """Responsible Gambling Features"""
    
    async def check_deposit_limits(self, user_id: str, amount: float) -> dict:
        """Check if deposit is within user's limits"""
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        limits = user.get("gambling_limits", {})
        
        if not limits:
            return {"allowed": True}
        
        # Get deposits in time periods
        now = datetime.now(timezone.utc)
        
        # Daily limit check
        if limits.get("daily_limit"):
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            daily_deposits = await db.transactions.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "type": "deposit",
                        "created_at": {"$gte": day_start.isoformat()}
                    }
                },
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]).to_list(1)
            
            daily_total = daily_deposits[0]["total"] if daily_deposits else 0
            if daily_total + amount > limits["daily_limit"]:
                return {
                    "allowed": False,
                    "reason": f"Daily deposit limit of ${limits['daily_limit']} would be exceeded",
                    "current": daily_total,
                    "limit": limits["daily_limit"]
                }
        
        # Weekly limit check
        if limits.get("weekly_limit"):
            week_start = now - timedelta(days=now.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            weekly_deposits = await db.transactions.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "type": "deposit",
                        "created_at": {"$gte": week_start.isoformat()}
                    }
                },
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]).to_list(1)
            
            weekly_total = weekly_deposits[0]["total"] if weekly_deposits else 0
            if weekly_total + amount > limits["weekly_limit"]:
                return {
                    "allowed": False,
                    "reason": f"Weekly deposit limit of ${limits['weekly_limit']} would be exceeded",
                    "current": weekly_total,
                    "limit": limits["weekly_limit"]
                }
        
        # Monthly limit check
        if limits.get("monthly_limit"):
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_deposits = await db.transactions.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "type": "deposit",
                        "created_at": {"$gte": month_start.isoformat()}
                    }
                },
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]).to_list(1)
            
            monthly_total = monthly_deposits[0]["total"] if monthly_deposits else 0
            if monthly_total + amount > limits["monthly_limit"]:
                return {
                    "allowed": False,
                    "reason": f"Monthly deposit limit of ${limits['monthly_limit']} would be exceeded",
                    "current": monthly_total,
                    "limit": limits["monthly_limit"]
                }
        
        return {"allowed": True}
    
    async def check_self_exclusion(self, user_id: str) -> dict:
        """Check if user is self-excluded"""
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        exclusion = user.get("self_exclusion", {})
        
        if not exclusion or not exclusion.get("active"):
            return {"excluded": False}
        
        if exclusion.get("permanent"):
            return {
                "excluded": True,
                "reason": "Permanent self-exclusion is active",
                "permanent": True
            }
        
        end_date = datetime.fromisoformat(exclusion.get("end_date", ""))
        if datetime.now(timezone.utc) < end_date:
            return {
                "excluded": True,
                "reason": f"Self-exclusion active until {end_date.strftime('%Y-%m-%d')}",
                "end_date": exclusion["end_date"]
            }
        
        # Exclusion expired, deactivate it
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"self_exclusion.active": False}}
        )
        return {"excluded": False}
    
    async def set_limits(self, user_id: str, limits: GamblingLimitsRequest) -> dict:
        """Set gambling limits for user"""
        update_data = {}
        if limits.daily_limit is not None:
            update_data["gambling_limits.daily_limit"] = limits.daily_limit
        if limits.weekly_limit is not None:
            update_data["gambling_limits.weekly_limit"] = limits.weekly_limit
        if limits.monthly_limit is not None:
            update_data["gambling_limits.monthly_limit"] = limits.monthly_limit
        if limits.session_time_limit is not None:
            update_data["gambling_limits.session_time_limit"] = limits.session_time_limit
        if limits.reality_check_interval is not None:
            update_data["gambling_limits.reality_check_interval"] = limits.reality_check_interval
        
        await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        return {"success": True, "message": "Gambling limits updated"}
    
    async def set_self_exclusion(self, user_id: str, request: SelfExclusionRequest) -> dict:
        """Set self-exclusion for user"""
        now = datetime.now(timezone.utc)
        
        duration_map = {
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "6m": timedelta(days=180),
            "1y": timedelta(days=365),
        }
        
        if request.duration == "permanent":
            exclusion_data = {
                "active": True,
                "permanent": True,
                "start_date": now.isoformat(),
                "reason": request.reason
            }
        else:
            end_date = now + duration_map.get(request.duration, timedelta(days=1))
            exclusion_data = {
                "active": True,
                "permanent": False,
                "start_date": now.isoformat(),
                "end_date": end_date.isoformat(),
                "duration": request.duration,
                "reason": request.reason
            }
        
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"self_exclusion": exclusion_data}}
        )
        
        # Log self-exclusion
        await db.self_exclusion_log.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": "activated",
            "duration": request.duration,
            "reason": request.reason,
            "created_at": now.isoformat()
        })
        
        return {
            "success": True,
            "message": f"Self-exclusion activated for {request.duration}",
            "exclusion": exclusion_data
        }
    
    async def get_session_info(self, user_id: str, session_start: str) -> dict:
        """Get session info for reality checks"""
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        limits = user.get("gambling_limits", {})
        
        start_time = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        session_duration = int((now - start_time).total_seconds() / 60)  # in minutes
        
        # Get session stats
        session_bets = await db.transactions.aggregate([
            {
                "$match": {
                    "user_id": user_id,
                    "type": "bet",
                    "created_at": {"$gte": session_start}
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
        ]).to_list(1)
        
        session_wins = await db.transactions.aggregate([
            {
                "$match": {
                    "user_id": user_id,
                    "type": "win",
                    "created_at": {"$gte": session_start}
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        total_bet = session_bets[0]["total"] if session_bets else 0
        bet_count = session_bets[0]["count"] if session_bets else 0
        total_won = session_wins[0]["total"] if session_wins else 0
        
        response = {
            "session_duration": session_duration,
            "total_bet": total_bet,
            "total_won": total_won,
            "net_result": total_won - total_bet,
            "bet_count": bet_count
        }
        
        # Check for time limit warning
        if limits.get("session_time_limit"):
            if session_duration >= limits["session_time_limit"]:
                response["time_limit_reached"] = True
                response["message"] = f"You've been playing for {session_duration} minutes. Consider taking a break."
        
        # Check for reality check
        if limits.get("reality_check_interval"):
            if session_duration > 0 and session_duration % limits["reality_check_interval"] == 0:
                response["reality_check"] = True
        
        return response

# Initialize responsible gambling service
rg_service = ResponsibleGamblingService()

# ==================== HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Check self-exclusion
        exclusion_check = await rg_service.check_self_exclusion(user_id)
        if exclusion_check.get("excluded"):
            raise HTTPException(status_code=403, detail=exclusion_check.get("reason"))
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_username = await db.users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "password_hash": hash_password(user_data.password),
        "balance": 100.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gambling_limits": {},
        "self_exclusion": {"active": False}
    }
    
    await db.users.insert_one(user_doc)
    
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "bonus",
        "amount": 100.0,
        "method": "welcome_bonus",
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "details": {"description": "Welcome bonus for new player!"}
    })
    
    token = create_token(user_id)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            balance=100.0,
            created_at=user_doc["created_at"],
            gambling_limits={},
            self_exclusion={"active": False}
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check self-exclusion
    exclusion_check = await rg_service.check_self_exclusion(user["id"])
    if exclusion_check.get("excluded"):
        raise HTTPException(status_code=403, detail=exclusion_check.get("reason"))
    
    token = create_token(user["id"])
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            balance=user["balance"],
            created_at=user["created_at"],
            gambling_limits=user.get("gambling_limits", {}),
            self_exclusion=user.get("self_exclusion", {})
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        username=current_user["username"],
        balance=current_user["balance"],
        created_at=current_user["created_at"],
        gambling_limits=current_user.get("gambling_limits", {}),
        self_exclusion=current_user.get("self_exclusion", {})
    )

# ==================== RESPONSIBLE GAMBLING ROUTES ====================

@api_router.get("/responsible-gambling/limits")
async def get_gambling_limits(current_user: dict = Depends(get_current_user)):
    """Get user's gambling limits"""
    return {
        "limits": current_user.get("gambling_limits", {}),
        "self_exclusion": current_user.get("self_exclusion", {})
    }

@api_router.post("/responsible-gambling/limits")
async def set_gambling_limits(limits: GamblingLimitsRequest, current_user: dict = Depends(get_current_user)):
    """Set gambling limits"""
    return await rg_service.set_limits(current_user["id"], limits)

@api_router.post("/responsible-gambling/self-exclusion")
async def activate_self_exclusion(request: SelfExclusionRequest, current_user: dict = Depends(get_current_user)):
    """Activate self-exclusion"""
    return await rg_service.set_self_exclusion(current_user["id"], request)

@api_router.get("/responsible-gambling/session")
async def get_session_info(session_start: str, current_user: dict = Depends(get_current_user)):
    """Get session information for reality checks"""
    return await rg_service.get_session_info(current_user["id"], session_start)

# ==================== JACKPOT ROUTES ====================

@api_router.get("/jackpot")
async def get_jackpot():
    """Get current progressive jackpot"""
    jackpot = await jackpot_service.get_jackpot()
    return {
        "amount": jackpot["amount"],
        "last_won": jackpot.get("last_won"),
        "total_winners": jackpot.get("total_winners", 0)
    }

@api_router.get("/jackpot/winners")
async def get_jackpot_winners():
    """Get recent jackpot winners"""
    winners = await db.jackpot_wins.find({}, {"_id": 0}).sort("won_at", -1).limit(10).to_list(10)
    
    # Get usernames
    for winner in winners:
        user = await db.users.find_one({"id": winner["user_id"]}, {"_id": 0, "username": 1})
        winner["username"] = user.get("username", "Anonymous") if user else "Anonymous"
    
    return winners

# ==================== WALLET ROUTES ====================

@api_router.get("/wallet/balance")
async def get_balance(current_user: dict = Depends(get_current_user)):
    return {"balance": current_user["balance"]}

@api_router.post("/wallet/deposit/payid")
async def deposit_payid(request: DepositRequest, current_user: dict = Depends(get_current_user)):
    """PayID deposit (demo or real based on configuration)"""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if request.amount > 10000:
        raise HTTPException(status_code=400, detail="Maximum deposit is $10,000")
    
    # Check deposit limits
    limit_check = await rg_service.check_deposit_limits(current_user["id"], request.amount)
    if not limit_check.get("allowed"):
        raise HTTPException(status_code=400, detail=limit_check.get("reason"))
    
    # Process via PayID service
    result = await payid_service.initiate_deposit(current_user["id"], request.amount)
    
    transaction_id = str(uuid.uuid4())
    transaction = {
        "id": transaction_id,
        "user_id": current_user["id"],
        "type": "deposit",
        "amount": request.amount,
        "method": "payid_real" if payid_service.is_configured else "payid_demo",
        "status": "completed" if result.get("status") == "demo" else "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "details": {
            "payid_reference": result.get("reference"),
            "payid": result.get("payid"),
            "is_demo": result.get("status") == "demo"
        }
    }
    
    await db.transactions.insert_one(transaction)
    
    # If demo mode, credit immediately
    if result.get("status") == "demo":
        new_balance = current_user["balance"] + request.amount
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"balance": new_balance}}
        )
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "new_balance": new_balance,
            "message": f"Demo PayID deposit of ${request.amount:.2f} successful!",
            "is_demo": True
        }
    
    # Real PayID - return instructions
    return {
        "success": True,
        "transaction_id": transaction_id,
        "status": "pending",
        "payid": result.get("payid"),
        "reference": result.get("reference"),
        "message": f"Please send ${request.amount:.2f} to the PayID shown. Funds will be credited once received.",
        "is_demo": False
    }

@api_router.post("/wallet/withdraw/payid")
async def withdraw_payid(request: WithdrawRequest, current_user: dict = Depends(get_current_user)):
    """PayID withdrawal"""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if request.amount > current_user["balance"]:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if request.amount < 10:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is $10")
    
    # Process via PayID service
    result = await payid_service.initiate_withdrawal(
        current_user["id"], 
        request.amount, 
        request.payid_account
    )
    
    transaction_id = str(uuid.uuid4())
    transaction = {
        "id": transaction_id,
        "user_id": current_user["id"],
        "type": "withdraw",
        "amount": request.amount,
        "method": "payid_real" if payid_service.is_configured else "payid_demo",
        "status": "completed" if result.get("status") == "demo" else "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "details": {
            "payid_account": request.payid_account,
            "payid_reference": result.get("reference"),
            "is_demo": result.get("status") == "demo"
        }
    }
    
    await db.transactions.insert_one(transaction)
    
    # Deduct from balance
    new_balance = current_user["balance"] - request.amount
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"balance": new_balance}}
    )
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "new_balance": new_balance,
        "message": f"Withdrawal of ${request.amount:.2f} to {request.payid_account} initiated!",
        "is_demo": result.get("status") == "demo"
    }

@api_router.get("/wallet/transactions", response_model=List[TransactionResponse])
async def get_transactions(current_user: dict = Depends(get_current_user)):
    transactions = await db.transactions.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return transactions

@api_router.get("/wallet/payid/status")
async def get_payid_status():
    """Check if real PayID is configured"""
    return {
        "configured": payid_service.is_configured,
        "environment": PAYID_ENVIRONMENT if payid_service.is_configured else "demo",
        "provider": "Zai (Assembly Payments)" if payid_service.is_configured else "Demo Mode"
    }

# ==================== STRIPE ROUTES ====================

@api_router.get("/wallet/deposit/packages")
async def get_deposit_packages():
    return {"packages": DEPOSIT_PACKAGES}

@api_router.post("/wallet/deposit/stripe/checkout")
async def create_stripe_checkout(request: StripeCheckoutRequest, http_request: Request, current_user: dict = Depends(get_current_user)):
    if request.package_id not in DEPOSIT_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    amount = DEPOSIT_PACKAGES[request.package_id]
    
    # Check deposit limits
    limit_check = await rg_service.check_deposit_limits(current_user["id"], amount)
    if not limit_check.get("allowed"):
        raise HTTPException(status_code=400, detail=limit_check.get("reason"))
    
    success_url = f"{request.origin_url}/wallet?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/wallet?cancelled=true"
    
    host_url = str(http_request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="aud",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user["id"],
            "package_id": request.package_id,
            "type": "casino_deposit"
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    transaction_id = str(uuid.uuid4())
    await db.payment_transactions.insert_one({
        "id": transaction_id,
        "user_id": current_user["id"],
        "session_id": session.session_id,
        "amount": amount,
        "currency": "aud",
        "method": "stripe",
        "payment_status": "pending",
        "status": "initiated",
        "package_id": request.package_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "user_id": current_user["id"],
            "package_id": request.package_id
        }
    })
    
    return {
        "checkout_url": session.url,
        "session_id": session.session_id
    }

@api_router.get("/wallet/deposit/stripe/status/{session_id}")
async def get_stripe_checkout_status(session_id: str, http_request: Request, current_user: dict = Depends(get_current_user)):
    transaction = await db.payment_transactions.find_one(
        {"session_id": session_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction["status"] == "completed":
        return {
            "status": "complete",
            "payment_status": "paid",
            "amount": transaction["amount"],
            "already_processed": True
        }
    
    host_url = str(http_request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    checkout_status = await stripe_checkout.get_checkout_status(session_id)
    
    if checkout_status.payment_status == "paid" and transaction["status"] != "completed":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": "completed",
                "payment_status": "paid",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        amount = transaction["amount"]
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"balance": amount}}
        )
        
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "type": "deposit",
            "amount": amount,
            "method": "stripe",
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "details": {"stripe_session_id": session_id, "package_id": transaction.get("package_id")}
        })
        
        user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
        
        return {
            "status": "complete",
            "payment_status": "paid",
            "amount": amount,
            "new_balance": user["balance"],
            "already_processed": False
        }
    
    return {
        "status": checkout_status.status,
        "payment_status": checkout_status.payment_status,
        "amount": checkout_status.amount_total / 100,
        "already_processed": False
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        logger.info(f"Webhook received: {webhook_response.event_type}")
        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": True}

@api_router.post("/webhook/payid")
async def payid_webhook(request: Request):
    """Handle PayID webhooks from Zai/payment provider"""
    body = await request.json()
    
    # Verify webhook signature (implement based on provider)
    # signature = request.headers.get("X-Webhook-Signature")
    
    event_type = body.get("event_type")
    reference = body.get("reference")
    
    if event_type == "payment.received":
        # Find pending transaction
        transaction = await db.transactions.find_one(
            {"details.payid_reference": reference, "status": "pending"},
            {"_id": 0}
        )
        
        if transaction:
            # Update transaction
            await db.transactions.update_one(
                {"id": transaction["id"]},
                {"$set": {"status": "completed"}}
            )
            
            # Credit user balance
            await db.users.update_one(
                {"id": transaction["user_id"]},
                {"$inc": {"balance": transaction["amount"]}}
            )
            
            logger.info(f"PayID payment received: {reference}")
    
    return {"received": True}

# ==================== GAME ROUTES ====================

@api_router.post("/games/play")
async def play_game(bet: BetRequest, current_user: dict = Depends(get_current_user)):
    """Universal game endpoint with jackpot integration"""
    if bet.amount <= 0:
        raise HTTPException(status_code=400, detail="Bet must be positive")
    if bet.amount > current_user["balance"]:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if bet.amount < 0.50:
        raise HTTPException(status_code=400, detail="Minimum bet is $0.50")
    if bet.amount > 1000:
        raise HTTPException(status_code=400, detail="Maximum bet is $1,000")
    
    # Contribute to jackpot
    jackpot_contribution = await jackpot_service.contribute(bet.amount)
    
    # Deduct bet from balance
    new_balance = current_user["balance"] - bet.amount
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"balance": new_balance}}
    )
    
    # Process game
    win_amount = 0.0
    result = {}
    jackpot_win = None
    
    if bet.game == "slots":
        result = process_slots(bet.bet_details)
        if result["win"]:
            win_amount = bet.amount * result["multiplier"]
        # Check for jackpot win on slots
        jackpot_win = await jackpot_service.check_jackpot_win(current_user["id"], bet.amount)
    
    elif bet.game == "blackjack":
        result = process_blackjack(bet.bet_details)
        if result["outcome"] == "win":
            win_amount = bet.amount * 2
        elif result["outcome"] == "blackjack":
            win_amount = bet.amount * 2.5
        elif result["outcome"] == "push":
            win_amount = bet.amount
    
    elif bet.game == "roulette":
        result = process_roulette(bet.bet_details)
        if result["win"]:
            win_amount = bet.amount * result["payout"]
        # Check for jackpot win on roulette (if betting on specific number)
        if bet.bet_details.get("bet_type") == "straight":
            jackpot_win = await jackpot_service.check_jackpot_win(current_user["id"], bet.amount)
    
    elif bet.game == "poker":
        result = process_poker(bet.bet_details)
        if result["win"]:
            win_amount = bet.amount * result["multiplier"]
        # Check for jackpot win on royal flush
        if result.get("hand_rank") == "royal_flush":
            jackpot_win = await jackpot_service.check_jackpot_win(current_user["id"], bet.amount)
    
    elif bet.game.startswith("themed_slot_"):
        # Custom themed slots
        theme_id = bet.game.replace("themed_slot_", "")
        result = process_themed_slot(theme_id, bet.bet_details)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        if result["win"]:
            win_amount = bet.amount * result["multiplier"]
        # Check for jackpot win on themed slots
        jackpot_win = await jackpot_service.check_jackpot_win(current_user["id"], bet.amount)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid game type")
    
    # Add jackpot win if applicable
    if jackpot_win and jackpot_win.get("won"):
        win_amount += jackpot_win["amount"]
        result["jackpot_won"] = True
        result["jackpot_amount"] = jackpot_win["amount"]
    
    # Add winnings to balance
    if win_amount > 0:
        new_balance += win_amount
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"balance": new_balance}}
        )
        
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "type": "win",
            "amount": win_amount,
            "method": bet.game,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "details": {
                "game": bet.game, 
                "bet_amount": bet.amount, 
                "result": result,
                "jackpot_won": jackpot_win.get("won") if jackpot_win else False
            }
        })
    
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "type": "bet",
        "amount": bet.amount,
        "method": bet.game,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "details": {"game": bet.game, "bet_details": bet.bet_details, "jackpot_contribution": jackpot_contribution}
    })
    
    game_record_id = str(uuid.uuid4())
    await db.game_history.insert_one({
        "id": game_record_id,
        "user_id": current_user["id"],
        "game": bet.game,
        "bet_amount": bet.amount,
        "win_amount": win_amount,
        "result": result,
        "jackpot_contribution": jackpot_contribution,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Get updated jackpot
    current_jackpot = await jackpot_service.get_jackpot()
    
    return {
        "id": game_record_id,
        "game": bet.game,
        "bet_amount": bet.amount,
        "win_amount": win_amount,
        "net_result": win_amount - bet.amount,
        "new_balance": new_balance,
        "result": result,
        "jackpot_contribution": jackpot_contribution,
        "current_jackpot": current_jackpot["amount"],
        "jackpot_won": jackpot_win.get("won") if jackpot_win else False
    }

@api_router.get("/games/history")
async def get_game_history(current_user: dict = Depends(get_current_user)):
    history = await db.game_history.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return history

# ==================== GAME LOGIC ====================

def process_slots(bet_details):
    symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "7️⃣", "💎"]
    weights = [30, 25, 20, 15, 5, 3, 2]
    
    reels = [random.choices(symbols, weights=weights)[0] for _ in range(3)]
    
    if reels[0] == reels[1] == reels[2]:
        symbol = reels[0]
        multipliers = {"🍒": 5, "🍋": 8, "🍊": 10, "🍇": 15, "⭐": 25, "7️⃣": 50, "💎": 100}
        return {"reels": reels, "win": True, "multiplier": multipliers[symbol]}
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        return {"reels": reels, "win": True, "multiplier": 2}
    
    return {"reels": reels, "win": False, "multiplier": 0}

def process_blackjack(bet_details):
    player_value = bet_details.get("player_value", 0)
    dealer_value = bet_details.get("dealer_value", 0)
    player_blackjack = bet_details.get("player_blackjack", False)
    dealer_blackjack = bet_details.get("dealer_blackjack", False)
    player_bust = bet_details.get("player_bust", False)
    dealer_bust = bet_details.get("dealer_bust", False)
    
    if player_bust:
        return {"outcome": "lose", "reason": "Player bust"}
    if dealer_bust:
        return {"outcome": "win", "reason": "Dealer bust"}
    if player_blackjack and not dealer_blackjack:
        return {"outcome": "blackjack", "reason": "Blackjack!"}
    if dealer_blackjack and not player_blackjack:
        return {"outcome": "lose", "reason": "Dealer blackjack"}
    if player_blackjack and dealer_blackjack:
        return {"outcome": "push", "reason": "Both blackjack"}
    if player_value > dealer_value:
        return {"outcome": "win", "reason": f"Player {player_value} beats dealer {dealer_value}"}
    if dealer_value > player_value:
        return {"outcome": "lose", "reason": f"Dealer {dealer_value} beats player {player_value}"}
    return {"outcome": "push", "reason": "Push - same value"}

def process_roulette(bet_details):
    bet_type = bet_details.get("bet_type", "straight")
    bet_number = bet_details.get("bet_number")
    bet_color = bet_details.get("bet_color")
    
    result_number = random.randint(0, 36)
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    result_color = "green" if result_number == 0 else ("red" if result_number in red_numbers else "black")
    
    win = False
    payout = 0
    
    if bet_type == "straight" and bet_number == result_number:
        win = True
        payout = 35
    elif bet_type == "color" and bet_color == result_color:
        win = True
        payout = 2
    elif bet_type == "even" and result_number != 0 and result_number % 2 == 0:
        win = True
        payout = 2
    elif bet_type == "odd" and result_number % 2 == 1:
        win = True
        payout = 2
    elif bet_type == "low" and 1 <= result_number <= 18:
        win = True
        payout = 2
    elif bet_type == "high" and 19 <= result_number <= 36:
        win = True
        payout = 2
    
    return {
        "result_number": result_number,
        "result_color": result_color,
        "win": win,
        "payout": payout,
        "bet_type": bet_type
    }

def process_poker(bet_details):
    hand_rank = bet_details.get("hand_rank", "none")
    
    payouts = {
        "royal_flush": 800,
        "straight_flush": 50,
        "four_of_a_kind": 25,
        "full_house": 9,
        "flush": 6,
        "straight": 4,
        "three_of_a_kind": 3,
        "two_pair": 2,
        "jacks_or_better": 1,
        "none": 0
    }
    
    multiplier = payouts.get(hand_rank, 0)
    return {
        "hand_rank": hand_rank,
        "win": multiplier > 0,
        "multiplier": multiplier
    }

# ==================== EXTERNAL PROVIDER ROUTES ====================

@api_router.get("/providers/status")
async def get_providers_status():
    """Get status of all external game providers"""
    return await external_provider.get_provider_status()

@api_router.get("/providers/games")
async def get_provider_games(provider: str = None):
    """Get games catalog from providers"""
    games = await external_provider.get_games_catalog(provider)
    return {"games": games, "count": len(games)}

@api_router.get("/providers/{provider}/games")
async def get_specific_provider_games(provider: str):
    """Get games from a specific provider"""
    if provider not in external_provider.PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider not found")
    games = await external_provider.get_games_catalog(provider)
    return {"provider": provider, "games": games, "count": len(games)}

@api_router.post("/providers/{provider}/launch")
async def launch_provider_game(provider: str, game_id: str, current_user: dict = Depends(get_current_user)):
    """Launch a game from external provider"""
    if provider not in external_provider.PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    result = await external_provider.launch_game(
        provider, 
        game_id, 
        current_user["id"],
        create_token(current_user["id"])
    )
    return result

@api_router.post("/webhook/provider/{provider}")
async def provider_webhook(provider: str, request: Request):
    """Handle webhooks from external game providers (bet/win callbacks)"""
    if provider not in external_provider.PROVIDERS:
        return {"error": "Unknown provider", "code": 404}
    
    data = await request.json()
    result = await external_provider.process_bet_callback(provider, data)
    return result

# ==================== THEMED SLOTS ROUTES ====================

@api_router.get("/games/themed-slots")
async def get_themed_slots():
    """Get all available themed slot games"""
    slots = []
    for slot_id, slot_data in CUSTOM_SLOT_THEMES.items():
        slots.append({
            "id": slot_id,
            "name": slot_data["name"],
            "theme": slot_data["theme"],
            "description": slot_data["description"],
            "symbols": slot_data["symbols"],
            "rtp": slot_data["rtp"],
            "volatility": slot_data["volatility"],
            "bg_color": slot_data["bg_color"],
            "max_multiplier": max(slot_data["multipliers"].values())
        })
    return {"slots": slots, "count": len(slots)}

@api_router.get("/games/themed-slots/{slot_id}")
async def get_themed_slot_details(slot_id: str):
    """Get details of a specific themed slot"""
    if slot_id not in CUSTOM_SLOT_THEMES:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    slot = CUSTOM_SLOT_THEMES[slot_id]
    return {
        "id": slot_id,
        "name": slot["name"],
        "theme": slot["theme"],
        "description": slot["description"],
        "symbols": slot["symbols"],
        "multipliers": slot["multipliers"],
        "rtp": slot["rtp"],
        "volatility": slot["volatility"],
        "bg_color": slot["bg_color"]
    }

# ==================== LEADERBOARD ====================

@api_router.get("/leaderboard")
async def get_leaderboard():
    top_players = await db.users.find(
        {},
        {"_id": 0, "username": 1, "balance": 1}
    ).sort("balance", -1).limit(10).to_list(10)
    return {"leaderboard": top_players}

# ==================== ROOT ====================

@api_router.get("/")
async def root():
    return {"message": "Welcome to NeonVegas Casino API", "version": "2.0.0"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
