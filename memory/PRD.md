# NeonVegas Casino - Product Requirements Document

## Original Problem Statement
Build an online casino where people can deposit and withdraw money through PayID. All casino games (Slots, Blackjack, Roulette, Poker). Both demo PayID and real Stripe payments. JWT-based custom auth. Vibrant, colorful design. Add slot games from providers JILI, Imperium, Slotomania, Rich.

## User Personas
- **Adult Casino Players**: Licensed gambling users looking for premium online gaming experience
- **New Players**: Users attracted by $100 welcome bonus
- **High Rollers**: Players using Stripe for larger deposits
- **Slot Enthusiasts**: Players looking for variety in slot themes and providers

## Core Requirements (Static)
- User authentication (JWT-based)
- Multiple casino games: Slots, Blackjack, Roulette, Video Poker + Themed Slots
- External provider integration (JILI, Imperium, Slotomania, Rich)
- Wallet with deposit/withdraw functionality
- PayID integration (demo + real structure)
- Stripe real payment integration
- Responsible gambling features
- Progressive jackpot system

## What's Been Implemented

### Phase 1 - MVP (Jan 2026)
- ✅ Full JWT authentication system with registration/login
- ✅ $100 welcome bonus for new users
- ✅ 4 core casino games (Slots, Blackjack, Roulette, Poker)
- ✅ PayID Demo deposits/withdrawals
- ✅ Stripe checkout integration with 5 packages
- ✅ Transaction history & Leaderboard
- ✅ NeonVegas vibrant cyberpunk theme

### Phase 2 - Enhanced Features (Jan 2026)
- ✅ Real PayID Integration Structure (Zai/Assembly Payments)
- ✅ Responsible Gambling Features (limits, self-exclusion)
- ✅ Progressive Jackpot System (2% contribution)

### Phase 3 - Expanded Slot Games (Jan 2026)
- ✅ **8 Custom Themed Slots**:
  - Pharaoh's Gold (Egyptian) - 100x max
  - Fortune Dragon (Asian) - 150x max
  - Lucky 7s (Classic) - 100x max
  - Ocean Treasure (Underwater) - 120x max
  - Fruit Frenzy (Fruit) - 80x max
  - Cosmic Cash (Space) - 150x max
  - Wild Safari (Safari) - 100x max
  - Mystic Gems (Fantasy) - 100x max

- ✅ **External Provider Integration Structure**:
  - JILI Games (6 demo games)
  - Imperium Games (4 demo games)
  - Slotomania (4 demo games)
  - Rich Games (4 demo games)

## Tech Stack
- **Frontend**: React, Tailwind CSS, Framer Motion, Shadcn UI
- **Backend**: FastAPI, MongoDB, JWT auth
- **Payments**: Stripe (real), PayID (demo + production-ready)

## API Keys Required for Production

### PayID (Zai/Assembly Payments)
```
PAYID_API_KEY=your_zai_api_key
PAYID_API_SECRET=your_zai_api_secret
PAYID_ENVIRONMENT=production
```

### External Game Providers
```
JILI_API_KEY=your_jili_key
JILI_API_SECRET=your_jili_secret
JILI_AGENT_ID=your_agent_id

IMPERIUM_API_KEY=your_imperium_key
IMPERIUM_API_SECRET=your_imperium_secret

SLOTOMANIA_API_KEY=your_slotomania_key
SLOTOMANIA_API_SECRET=your_slotomania_secret

RICH_API_KEY=your_rich_key
RICH_API_SECRET=your_rich_secret
```

## Game Summary
| Category | Count | Details |
|----------|-------|---------|
| Core Games | 4 | Slots, Blackjack, Roulette, Poker |
| Themed Slots | 8 | Custom in-house themed games |
| JILI Games | 6 | Demo mode (needs API key) |
| Imperium Games | 4 | Demo mode (needs API key) |
| Slotomania | 4 | Demo mode (needs API key) |
| Rich Games | 4 | Demo mode (needs API key) |
| **Total** | **30** | Mix of in-house and provider games |

## P0/P1/P2 Backlog

### P0 (Done)
- Core auth, games, wallet, payments
- Responsible gambling features
- Progressive jackpot
- Themed slots
- Provider integration structure

### P1 (Next Phase)
- Add real provider API keys for live games
- Real PayID via Zai
- More themed slot games
- Player rewards/VIP program

### P2 (Future)
- Live dealer games
- Multiplayer poker rooms
- Mobile app
- Sports betting
