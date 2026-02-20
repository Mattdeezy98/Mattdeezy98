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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Wallet Models
class DepositRequest(BaseModel):
    amount: float
    method: str  # "payid_demo" or "stripe"

class WithdrawRequest(BaseModel):
    amount: float
    payid_account: str  # Demo PayID account

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
    bet_details: dict  # Game-specific bet details

class GameResultResponse(BaseModel):
    id: str
    game: str
    bet_amount: float
    win_amount: float
    result: dict
    created_at: str

# Stripe Models
class StripeCheckoutRequest(BaseModel):
    package_id: str  # small, medium, large, xl, xxl
    origin_url: str

# Fixed deposit packages (amounts in AUD)
DEPOSIT_PACKAGES = {
    "small": 10.0,
    "medium": 25.0,
    "large": 50.0,
    "xl": 100.0,
    "xxl": 250.0
}

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
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username already exists
    existing_username = await db.users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "password_hash": hash_password(user_data.password),
        "balance": 100.0,  # Welcome bonus!
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create welcome bonus transaction
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
            created_at=user_doc["created_at"]
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user["id"])
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            balance=user["balance"],
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        username=current_user["username"],
        balance=current_user["balance"],
        created_at=current_user["created_at"]
    )

# ==================== WALLET ROUTES ====================

@api_router.get("/wallet/balance")
async def get_balance(current_user: dict = Depends(get_current_user)):
    return {"balance": current_user["balance"]}

@api_router.post("/wallet/deposit/payid")
async def deposit_payid_demo(request: DepositRequest, current_user: dict = Depends(get_current_user)):
    """Demo PayID deposit - instantly adds funds"""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if request.amount > 10000:
        raise HTTPException(status_code=400, detail="Maximum deposit is $10,000")
    
    # Create transaction
    transaction_id = str(uuid.uuid4())
    transaction = {
        "id": transaction_id,
        "user_id": current_user["id"],
        "type": "deposit",
        "amount": request.amount,
        "method": "payid_demo",
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "details": {"payid_reference": f"DEMO-{transaction_id[:8].upper()}"}
    }
    
    await db.transactions.insert_one(transaction)
    
    # Update user balance
    new_balance = current_user["balance"] + request.amount
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"balance": new_balance}}
    )
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "new_balance": new_balance,
        "message": f"Demo PayID deposit of ${request.amount:.2f} successful!"
    }

@api_router.post("/wallet/withdraw/payid")
async def withdraw_payid_demo(request: WithdrawRequest, current_user: dict = Depends(get_current_user)):
    """Demo PayID withdrawal"""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if request.amount > current_user["balance"]:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if request.amount < 10:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is $10")
    
    # Create transaction
    transaction_id = str(uuid.uuid4())
    transaction = {
        "id": transaction_id,
        "user_id": current_user["id"],
        "type": "withdraw",
        "amount": request.amount,
        "method": "payid_demo",
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "details": {
            "payid_account": request.payid_account,
            "payid_reference": f"WD-{transaction_id[:8].upper()}"
        }
    }
    
    await db.transactions.insert_one(transaction)
    
    # Update user balance
    new_balance = current_user["balance"] - request.amount
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"balance": new_balance}}
    )
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "new_balance": new_balance,
        "message": f"Withdrawal of ${request.amount:.2f} to {request.payid_account} initiated!"
    }

@api_router.get("/wallet/transactions", response_model=List[TransactionResponse])
async def get_transactions(current_user: dict = Depends(get_current_user)):
    transactions = await db.transactions.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return transactions

# ==================== STRIPE ROUTES ====================

@api_router.get("/wallet/deposit/packages")
async def get_deposit_packages():
    """Get available deposit packages"""
    return {"packages": DEPOSIT_PACKAGES}

@api_router.post("/wallet/deposit/stripe/checkout")
async def create_stripe_checkout(request: StripeCheckoutRequest, http_request: Request, current_user: dict = Depends(get_current_user)):
    """Create Stripe checkout session"""
    if request.package_id not in DEPOSIT_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    amount = DEPOSIT_PACKAGES[request.package_id]
    
    # Build URLs from provided origin
    success_url = f"{request.origin_url}/wallet?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/wallet?cancelled=true"
    
    # Initialize Stripe
    host_url = str(http_request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    # Create checkout session
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
    
    # Create pending transaction record
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
    """Check Stripe checkout status and update balance if paid"""
    
    # Find the transaction
    transaction = await db.payment_transactions.find_one(
        {"session_id": session_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # If already processed, return cached status
    if transaction["status"] == "completed":
        return {
            "status": "complete",
            "payment_status": "paid",
            "amount": transaction["amount"],
            "already_processed": True
        }
    
    # Initialize Stripe and check status
    host_url = str(http_request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    checkout_status = await stripe_checkout.get_checkout_status(session_id)
    
    # If paid and not yet processed
    if checkout_status.payment_status == "paid" and transaction["status"] != "completed":
        # Update payment transaction
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": "completed",
                "payment_status": "paid",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Add to user's balance
        amount = transaction["amount"]
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"balance": amount}}
        )
        
        # Create transaction record
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
        
        # Get updated balance
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
        "amount": checkout_status.amount_total / 100,  # Convert from cents
        "already_processed": False
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
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

# ==================== GAME ROUTES ====================

@api_router.post("/games/play")
async def play_game(bet: BetRequest, current_user: dict = Depends(get_current_user)):
    """Universal game endpoint"""
    if bet.amount <= 0:
        raise HTTPException(status_code=400, detail="Bet must be positive")
    if bet.amount > current_user["balance"]:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if bet.amount < 0.50:
        raise HTTPException(status_code=400, detail="Minimum bet is $0.50")
    if bet.amount > 1000:
        raise HTTPException(status_code=400, detail="Maximum bet is $1,000")
    
    # Deduct bet from balance
    new_balance = current_user["balance"] - bet.amount
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"balance": new_balance}}
    )
    
    # Process game based on type
    import random
    win_amount = 0.0
    result = {}
    
    if bet.game == "slots":
        result = process_slots(bet.bet_details)
        if result["win"]:
            win_amount = bet.amount * result["multiplier"]
    
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
    
    elif bet.game == "poker":
        result = process_poker(bet.bet_details)
        if result["win"]:
            win_amount = bet.amount * result["multiplier"]
    
    else:
        raise HTTPException(status_code=400, detail="Invalid game type")
    
    # Add winnings to balance
    if win_amount > 0:
        new_balance += win_amount
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"balance": new_balance}}
        )
        
        # Record win transaction
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "type": "win",
            "amount": win_amount,
            "method": bet.game,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "details": {"game": bet.game, "bet_amount": bet.amount, "result": result}
        })
    
    # Record bet transaction
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "type": "bet",
        "amount": bet.amount,
        "method": bet.game,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "details": {"game": bet.game, "bet_details": bet.bet_details}
    })
    
    # Save game history
    game_record_id = str(uuid.uuid4())
    await db.game_history.insert_one({
        "id": game_record_id,
        "user_id": current_user["id"],
        "game": bet.game,
        "bet_amount": bet.amount,
        "win_amount": win_amount,
        "result": result,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "id": game_record_id,
        "game": bet.game,
        "bet_amount": bet.amount,
        "win_amount": win_amount,
        "net_result": win_amount - bet.amount,
        "new_balance": new_balance,
        "result": result
    }

@api_router.get("/games/history")
async def get_game_history(current_user: dict = Depends(get_current_user)):
    history = await db.game_history.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return history

# ==================== GAME LOGIC ====================

import random

def process_slots(bet_details):
    """Process slot machine spin"""
    symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "7️⃣", "💎"]
    weights = [30, 25, 20, 15, 5, 3, 2]  # Lower weight = rarer
    
    reels = [random.choices(symbols, weights=weights)[0] for _ in range(3)]
    
    # Check for wins
    if reels[0] == reels[1] == reels[2]:
        symbol = reels[0]
        multipliers = {"🍒": 5, "🍋": 8, "🍊": 10, "🍇": 15, "⭐": 25, "7️⃣": 50, "💎": 100}
        return {"reels": reels, "win": True, "multiplier": multipliers[symbol]}
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        return {"reels": reels, "win": True, "multiplier": 2}
    
    return {"reels": reels, "win": False, "multiplier": 0}

def process_blackjack(bet_details):
    """Process blackjack game result"""
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
    """Process roulette spin"""
    bet_type = bet_details.get("bet_type", "straight")
    bet_number = bet_details.get("bet_number")
    bet_color = bet_details.get("bet_color")
    
    # Spin the wheel
    result_number = random.randint(0, 36)
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    result_color = "green" if result_number == 0 else ("red" if result_number in red_numbers else "black")
    
    # Check bet
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
    """Process video poker game result"""
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
    """Get top players by balance"""
    top_players = await db.users.find(
        {},
        {"_id": 0, "username": 1, "balance": 1}
    ).sort("balance", -1).limit(10).to_list(10)
    
    return {"leaderboard": top_players}

# ==================== ROOT ====================

@api_router.get("/")
async def root():
    return {"message": "Welcome to NeonVegas Casino API", "version": "1.0.0"}

# Include the router in the main app
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
