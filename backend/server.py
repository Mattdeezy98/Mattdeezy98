from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
import random
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
PAYID_ENVIRONMENT = os.environ.get('PAYID_ENVIRONMENT', 'sandbox')  # sandbox or production
PAYID_WEBHOOK_SECRET = os.environ.get('PAYID_WEBHOOK_SECRET', '')

# Jackpot Configuration
JACKPOT_CONTRIBUTION_RATE = 0.02  # 2% of each bet goes to jackpot
JACKPOT_WIN_PROBABILITY = 0.0001  # 0.01% chance per spin to win jackpot
MINIMUM_JACKPOT = 1000.0  # Minimum jackpot amount

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
        
        start_time = datetime.fromisoformat(session_start)
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
