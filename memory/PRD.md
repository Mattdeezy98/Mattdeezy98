# NeonVegas Casino - Product Requirements Document

## Original Problem Statement
Build an online casino where people can deposit and withdraw money through PayID. All casino games (Slots, Blackjack, Roulette, Poker). Both demo PayID and real Stripe payments. JWT-based custom auth (email/password). Vibrant, colorful design.

## User Personas
- **Adult Casino Players**: Licensed gambling users looking for premium online gaming experience
- **New Players**: Users attracted by $100 welcome bonus
- **High Rollers**: Players using Stripe for larger deposits
- **Responsible Gamblers**: Players who want to set limits and play responsibly

## Core Requirements (Static)
- User authentication (JWT-based)
- 4 casino games: Slots, Blackjack, Roulette, Video Poker
- Wallet with deposit/withdraw functionality
- PayID integration (demo + real structure)
- Stripe real payment integration
- Transaction history tracking
- Responsible gambling features
- Progressive jackpot system
- Vibrant NeonVegas theme

## What's Been Implemented (Jan 2026)

### Phase 1 - MVP
- ✅ Full JWT authentication system with registration/login
- ✅ $100 welcome bonus for new users
- ✅ 4 fully playable casino games (Slots, Blackjack, Roulette, Poker)
- ✅ PayID Demo deposits (instant, up to $10,000)
- ✅ PayID Demo withdrawals (min $10)
- ✅ Stripe checkout integration with 5 packages ($10-$250)
- ✅ Transaction history
- ✅ Leaderboard
- ✅ NeonVegas vibrant cyberpunk theme

### Phase 2 - Enhanced Features (Jan 2026)
- ✅ **Real PayID Integration Structure** - Production-ready with Zai (Assembly Payments) API placeholders
  - Add PAYID_API_KEY, PAYID_API_SECRET to .env to enable
  - Supports deposits, withdrawals, webhooks
  - Demo mode when keys not configured
- ✅ **Responsible Gambling Features**
  - Daily/weekly/monthly deposit limits
  - Session time limits
  - Reality check intervals
  - Self-exclusion (24h to permanent)
  - Session info tracking
- ✅ **Progressive Jackpot System**
  - 2% of every bet contributes to jackpot
  - Minimum jackpot: $1,000
  - Random chance to win on slots/roulette/poker
  - Jackpot display on lobby and games

## Tech Stack
- **Frontend**: React, Tailwind CSS, Framer Motion, Shadcn UI
- **Backend**: FastAPI, MongoDB, JWT auth
- **Payments**: Stripe (real), PayID (demo + production-ready structure)

## API Keys Required for Production PayID
```
PAYID_API_KEY=your_zai_api_key
PAYID_API_SECRET=your_zai_api_secret
PAYID_ENVIRONMENT=production
PAYID_WEBHOOK_SECRET=your_webhook_secret
```

## P0/P1/P2 Backlog

### P0 (Done)
- Core auth, games, wallet, payments
- Responsible gambling features
- Progressive jackpot
- PayID real integration structure

### P1 (Next Phase)
- Get real Zai/Assembly Payments API keys
- Real PayID deposit/withdrawal testing
- Game statistics dashboard
- Player rewards/VIP program

### P2 (Future)
- Live dealer games
- Multiplayer poker rooms
- Mobile app
- More casino games
