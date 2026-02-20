# NeonVegas Casino - Product Requirements Document

## Original Problem Statement
Build an online casino where people can deposit and withdraw money through PayID. All casino games (Slots, Blackjack, Roulette, Poker). Both demo PayID and real Stripe payments. JWT-based custom auth (email/password). Vibrant, colorful design.

## User Personas
- **Adult Casino Players**: Licensed gambling users looking for premium online gaming experience
- **New Players**: Users attracted by $100 welcome bonus
- **High Rollers**: Players using Stripe for larger deposits

## Core Requirements
- User authentication (JWT-based)
- 4 casino games: Slots, Blackjack, Roulette, Video Poker
- Wallet with deposit/withdraw functionality
- PayID demo system (instant transactions)
- Stripe real payment integration
- Transaction history tracking
- Vibrant NeonVegas theme

## What's Been Implemented (Jan 2026)
- ✅ Full JWT authentication system with registration/login
- ✅ $100 welcome bonus for new users
- ✅ 4 fully playable casino games
- ✅ PayID Demo deposits (instant, up to $10,000)
- ✅ PayID Demo withdrawals (min $10)
- ✅ Stripe checkout integration with 5 packages ($10-$250)
- ✅ Transaction history
- ✅ Leaderboard
- ✅ NeonVegas vibrant cyberpunk theme

## Tech Stack
- **Frontend**: React, Tailwind CSS, Framer Motion, Shadcn UI
- **Backend**: FastAPI, MongoDB, JWT auth
- **Payments**: Stripe (real), PayID (demo/simulated)

## P0/P1/P2 Backlog
### P0 (Done)
- Core auth, games, wallet, payments

### P1 (Next Phase)
- Real PayID integration via payment gateway
- Game statistics and analytics
- Responsible gambling limits

### P2 (Future)
- Live dealer games
- Multiplayer poker rooms
- VIP loyalty program
- Mobile app
