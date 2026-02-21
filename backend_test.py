import requests
import sys
import json
from datetime import datetime

class NeonVegasCasinoTester:
    def __init__(self, base_url="https://instant-bet-zone.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    self.log_test(name, True)
                    return True, response_data
                except:
                    self.log_test(name, True, "No JSON response")
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    error_msg = f"Status {response.status_code}, Expected {expected_status}. Response: {error_data}"
                except:
                    error_msg = f"Status {response.status_code}, Expected {expected_status}. Response: {response.text[:200]}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            self.log_test(name, False, error_msg)
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_user_registration(self):
        """Test user registration with welcome bonus"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user = {
            "email": f"testuser{timestamp}@casino.com",
            "password": "test123",
            "username": f"TestGamer{timestamp}"
        }
        
        success, response = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200, 
            test_user
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            print(f"   ✅ User registered with ID: {self.user_data['id']}")
            print(f"   ✅ Welcome bonus: ${self.user_data['balance']}")
            
            # Verify welcome bonus is $100
            if self.user_data['balance'] == 100.0:
                self.log_test("Welcome Bonus Amount", True)
            else:
                self.log_test("Welcome Bonus Amount", False, f"Expected $100, got ${self.user_data['balance']}")
            
            return True
        return False

    def test_user_login(self):
        """Test user login"""
        if not self.user_data:
            self.log_test("User Login", False, "No user data available for login test")
            return False
            
        login_data = {
            "email": self.user_data['email'],
            "password": "test123"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            login_data
        )
        
        if success and 'access_token' in response:
            print(f"   ✅ Login successful for user: {response['user']['username']}")
            return True
        return False

    def test_get_user_profile(self):
        """Test get current user profile"""
        return self.run_test("Get User Profile", "GET", "auth/me", 200)

    def test_wallet_balance(self):
        """Test get wallet balance"""
        return self.run_test("Get Wallet Balance", "GET", "wallet/balance", 200)

    def test_payid_deposit(self):
        """Test PayID demo deposit"""
        deposit_data = {
            "amount": 50.0,
            "method": "payid_demo"
        }
        
        success, response = self.run_test(
            "PayID Demo Deposit",
            "POST",
            "wallet/deposit/payid",
            200,
            deposit_data
        )
        
        if success and response.get('success'):
            print(f"   ✅ Deposit successful, new balance: ${response.get('new_balance')}")
            return True
        return False

    def test_payid_withdrawal(self):
        """Test PayID demo withdrawal"""
        withdraw_data = {
            "amount": 25.0,
            "payid_account": "testuser@example.com"
        }
        
        success, response = self.run_test(
            "PayID Demo Withdrawal",
            "POST",
            "wallet/withdraw/payid",
            200,
            withdraw_data
        )
        
        if success and response.get('success'):
            print(f"   ✅ Withdrawal successful, new balance: ${response.get('new_balance')}")
            return True
        return False

    def test_transaction_history(self):
        """Test get transaction history"""
        return self.run_test("Transaction History", "GET", "wallet/transactions", 200)

    def test_deposit_packages(self):
        """Test get deposit packages for Stripe"""
        return self.run_test("Deposit Packages", "GET", "wallet/deposit/packages", 200)

    def test_stripe_checkout_creation(self):
        """Test Stripe checkout session creation"""
        checkout_data = {
            "package_id": "medium",
            "origin_url": "https://instant-bet-zone.preview.emergentagent.com"
        }
        
        success, response = self.run_test(
            "Stripe Checkout Creation",
            "POST",
            "wallet/deposit/stripe/checkout",
            200,
            checkout_data
        )
        
        if success and 'checkout_url' in response:
            print(f"   ✅ Checkout URL created: {response['checkout_url'][:50]}...")
            return True
        return False

    def test_slots_game(self):
        """Test slots game play"""
        game_data = {
            "game": "slots",
            "amount": 5.0,
            "bet_details": {}
        }
        
        success, response = self.run_test(
            "Slots Game Play",
            "POST",
            "games/play",
            200,
            game_data
        )
        
        if success and 'result' in response:
            print(f"   ✅ Slots result: {response['result']}")
            print(f"   ✅ Win amount: ${response.get('win_amount', 0)}")
            return True
        return False

    def test_blackjack_game(self):
        """Test blackjack game play"""
        game_data = {
            "game": "blackjack",
            "amount": 10.0,
            "bet_details": {
                "player_value": 20,
                "dealer_value": 18,
                "player_blackjack": False,
                "dealer_blackjack": False,
                "player_bust": False,
                "dealer_bust": False
            }
        }
        
        success, response = self.run_test(
            "Blackjack Game Play",
            "POST",
            "games/play",
            200,
            game_data
        )
        
        if success and 'result' in response:
            print(f"   ✅ Blackjack result: {response['result']}")
            print(f"   ✅ Win amount: ${response.get('win_amount', 0)}")
            return True
        return False

    def test_roulette_game(self):
        """Test roulette game play"""
        game_data = {
            "game": "roulette",
            "amount": 5.0,
            "bet_details": {
                "bet_type": "color",
                "bet_color": "red"
            }
        }
        
        success, response = self.run_test(
            "Roulette Game Play",
            "POST",
            "games/play",
            200,
            game_data
        )
        
        if success and 'result' in response:
            print(f"   ✅ Roulette result: {response['result']}")
            print(f"   ✅ Win amount: ${response.get('win_amount', 0)}")
            return True
        return False

    def test_poker_game(self):
        """Test poker game play"""
        game_data = {
            "game": "poker",
            "amount": 2.0,
            "bet_details": {
                "hand_rank": "jacks_or_better"
            }
        }
        
        success, response = self.run_test(
            "Poker Game Play",
            "POST",
            "games/play",
            200,
            game_data
        )
        
        if success and 'result' in response:
            print(f"   ✅ Poker result: {response['result']}")
            print(f"   ✅ Win amount: ${response.get('win_amount', 0)}")
            return True
        return False

    def test_game_history(self):
        """Test get game history"""
        return self.run_test("Game History", "GET", "games/history", 200)

    def test_leaderboard(self):
        """Test get leaderboard"""
        return self.run_test("Leaderboard", "GET", "leaderboard", 200)

    def test_jackpot_api(self):
        """Test jackpot API"""
        success, response = self.run_test("Get Jackpot", "GET", "jackpot", 200)
        
        if success and 'amount' in response:
            print(f"   ✅ Current jackpot: ${response['amount']}")
            # Verify minimum jackpot is $1000
            if response['amount'] >= 1000:
                self.log_test("Jackpot Minimum Amount", True)
            else:
                self.log_test("Jackpot Minimum Amount", False, f"Expected >= $1000, got ${response['amount']}")
            return True
        return False

    def test_jackpot_winners(self):
        """Test jackpot winners API"""
        return self.run_test("Get Jackpot Winners", "GET", "jackpot/winners", 200)

    def test_payid_status(self):
        """Test PayID status API"""
        success, response = self.run_test("PayID Status", "GET", "wallet/payid/status", 200)
        
        if success and 'configured' in response:
            print(f"   ✅ PayID configured: {response['configured']}")
            print(f"   ✅ PayID environment: {response.get('environment', 'unknown')}")
            print(f"   ✅ PayID provider: {response.get('provider', 'unknown')}")
            
            # Verify it's in demo mode (since API keys are empty)
            if not response['configured'] and response.get('environment') == 'demo':
                self.log_test("PayID Demo Mode", True)
            else:
                self.log_test("PayID Demo Mode", False, f"Expected demo mode, got configured={response['configured']}")
            return True
        return False

    def test_responsible_gambling_limits_get(self):
        """Test get responsible gambling limits"""
        success, response = self.run_test("Get RG Limits", "GET", "responsible-gambling/limits", 200)
        
        if success and 'limits' in response:
            print(f"   ✅ Current limits: {response['limits']}")
            print(f"   ✅ Self-exclusion status: {response.get('self_exclusion', {})}")
            return True
        return False

    def test_responsible_gambling_limits_set(self):
        """Test set responsible gambling limits"""
        limits_data = {
            "daily_limit": 100.0,
            "weekly_limit": 500.0,
            "monthly_limit": 2000.0,
            "session_time_limit": 120,
            "reality_check_interval": 30
        }
        
        success, response = self.run_test(
            "Set RG Limits",
            "POST",
            "responsible-gambling/limits",
            200,
            limits_data
        )
        
        if success and response.get('success'):
            print(f"   ✅ Limits updated successfully")
            return True
        return False

    def test_responsible_gambling_session(self):
        """Test get session info for reality checks"""
        # Use current time as session start
        session_start = datetime.now().isoformat()
        
        success, response = self.run_test(
            "Get Session Info",
            "GET",
            f"responsible-gambling/session?session_start={session_start}",
            200
        )
        
        if success and 'session_duration' in response:
            print(f"   ✅ Session duration: {response['session_duration']} minutes")
            print(f"   ✅ Total bet: ${response.get('total_bet', 0)}")
            print(f"   ✅ Net result: ${response.get('net_result', 0)}")
            return True
        return False

    def test_enhanced_slots_game(self):
        """Test enhanced slots game with jackpot contribution"""
        game_data = {
            "game": "slots",
            "amount": 10.0,
            "bet_details": {}
        }
        
        success, response = self.run_test(
            "Enhanced Slots Game",
            "POST",
            "games/play",
            200,
            game_data
        )
        
        if success and 'result' in response:
            print(f"   ✅ Slots result: {response['result']}")
            print(f"   ✅ Win amount: ${response.get('win_amount', 0)}")
            print(f"   ✅ Jackpot contribution: ${response.get('jackpot_contribution', 0)}")
            print(f"   ✅ Current jackpot: ${response.get('current_jackpot', 0)}")
            
            # Verify jackpot contribution is 2% of bet
            expected_contribution = game_data['amount'] * 0.02
            actual_contribution = response.get('jackpot_contribution', 0)
            if abs(actual_contribution - expected_contribution) < 0.01:
                self.log_test("Jackpot Contribution Rate", True)
            else:
                self.log_test("Jackpot Contribution Rate", False, 
                            f"Expected ${expected_contribution:.2f}, got ${actual_contribution:.2f}")
            
            return True
        return False

    def test_providers_status(self):
        """Test providers status API - should return all 4 providers"""
        success, response = self.run_test("Providers Status", "GET", "providers/status", 200)
        
        if success and isinstance(response, dict):
            expected_providers = ["jili", "imperium", "slotomania", "rich"]
            found_providers = list(response.keys())
            
            print(f"   ✅ Found providers: {found_providers}")
            
            # Check if all 4 providers are present
            missing_providers = [p for p in expected_providers if p not in found_providers]
            if not missing_providers:
                self.log_test("All 4 Providers Present", True)
                
                # Check provider details
                for provider_id, info in response.items():
                    if provider_id in expected_providers:
                        print(f"   ✅ {provider_id}: {info.get('name')} - {info.get('mode')} mode - {info.get('games_count')} games")
                        
                        # Verify provider has required fields
                        required_fields = ['name', 'configured', 'mode', 'games_count']
                        if all(field in info for field in required_fields):
                            self.log_test(f"Provider {provider_id} Structure", True)
                        else:
                            self.log_test(f"Provider {provider_id} Structure", False, f"Missing fields: {[f for f in required_fields if f not in info]}")
                
                return True
            else:
                self.log_test("All 4 Providers Present", False, f"Missing providers: {missing_providers}")
                return False
        return False

    def test_providers_games(self):
        """Test providers games API - should return games from all providers"""
        success, response = self.run_test("Providers Games", "GET", "providers/games", 200)
        
        if success and 'games' in response:
            games = response['games']
            print(f"   ✅ Total games found: {len(games)}")
            
            # Check games by provider
            providers_with_games = {}
            for game in games:
                provider = game.get('provider')
                if provider:
                    if provider not in providers_with_games:
                        providers_with_games[provider] = 0
                    providers_with_games[provider] += 1
            
            print(f"   ✅ Games by provider: {providers_with_games}")
            
            # Verify all 4 providers have games
            expected_providers = ["jili", "imperium", "slotomania", "rich"]
            missing_providers = [p for p in expected_providers if p not in providers_with_games]
            
            if not missing_providers:
                self.log_test("All Providers Have Games", True)
                
                # Check game structure
                if games:
                    sample_game = games[0]
                    required_fields = ['id', 'name', 'type', 'provider']
                    if all(field in sample_game for field in required_fields):
                        self.log_test("Game Structure Valid", True)
                    else:
                        self.log_test("Game Structure Valid", False, f"Missing fields in game: {[f for f in required_fields if f not in sample_game]}")
                
                return True
            else:
                self.log_test("All Providers Have Games", False, f"Providers without games: {missing_providers}")
                return False
        return False

    def test_themed_slots_list(self):
        """Test themed slots list API - should return 8 themed slots"""
        success, response = self.run_test("Themed Slots List", "GET", "games/themed-slots", 200)
        
        if success and 'slots' in response:
            slots = response['slots']
            print(f"   ✅ Total themed slots found: {len(slots)}")
            
            # Verify we have 8 themed slots
            if len(slots) == 8:
                self.log_test("8 Themed Slots Present", True)
                
                # Check slot structure and themes
                themes_found = []
                for slot in slots:
                    theme = slot.get('theme')
                    if theme:
                        themes_found.append(theme)
                    
                    # Check required fields
                    required_fields = ['id', 'name', 'theme', 'description', 'symbols', 'rtp']
                    if all(field in slot for field in required_fields):
                        self.log_test(f"Themed Slot {slot.get('id')} Structure", True)
                    else:
                        self.log_test(f"Themed Slot {slot.get('id')} Structure", False, f"Missing fields: {[f for f in required_fields if f not in slot]}")
                
                print(f"   ✅ Themes found: {themes_found}")
                
                # Verify expected themes are present
                expected_themes = ["egyptian", "asian", "classic", "underwater", "fruit", "space", "safari", "fantasy"]
                missing_themes = [t for t in expected_themes if t not in themes_found]
                if not missing_themes:
                    self.log_test("All Expected Themes Present", True)
                else:
                    self.log_test("All Expected Themes Present", False, f"Missing themes: {missing_themes}")
                
                return True
            else:
                self.log_test("8 Themed Slots Present", False, f"Expected 8 slots, found {len(slots)}")
                return False
        return False

    def test_themed_slot_details(self):
        """Test themed slot details API - pharaohs_gold"""
        success, response = self.run_test("Themed Slot Details", "GET", "games/themed-slots/pharaohs_gold", 200)
        
        if success and 'id' in response:
            slot = response
            print(f"   ✅ Slot details: {slot.get('name')} - {slot.get('theme')} theme")
            print(f"   ✅ RTP: {slot.get('rtp')}% - Volatility: {slot.get('volatility')}")
            print(f"   ✅ Symbols: {slot.get('symbols')}")
            
            # Verify it's the pharaohs_gold slot
            if slot.get('id') == 'pharaohs_gold' and slot.get('theme') == 'egyptian':
                self.log_test("Pharaohs Gold Slot Details", True)
                
                # Check required fields
                required_fields = ['id', 'name', 'theme', 'description', 'symbols', 'multipliers', 'rtp', 'volatility']
                missing_fields = [f for f in required_fields if f not in slot]
                if not missing_fields:
                    self.log_test("Pharaohs Gold Complete Structure", True)
                else:
                    self.log_test("Pharaohs Gold Complete Structure", False, f"Missing fields: {missing_fields}")
                
                return True
            else:
                self.log_test("Pharaohs Gold Slot Details", False, f"Expected pharaohs_gold/egyptian, got {slot.get('id')}/{slot.get('theme')}")
                return False
        return False

    def test_themed_slot_gameplay(self):
        """Test themed slot gameplay - fortune_dragon"""
        game_data = {
            "game": "themed_slot_fortune_dragon",
            "amount": 5.0,
            "bet_details": {}
        }
        
        success, response = self.run_test(
            "Themed Slot Gameplay",
            "POST",
            "games/play",
            200,
            game_data
        )
        
        if success and 'result' in response:
            result = response['result']
            print(f"   ✅ Themed slot result: {result}")
            print(f"   ✅ Win amount: ${response.get('win_amount', 0)}")
            print(f"   ✅ Jackpot contribution: ${response.get('jackpot_contribution', 0)}")
            
            # Verify result structure
            required_fields = ['reels', 'win', 'theme', 'theme_name']
            missing_fields = [f for f in required_fields if f not in result]
            if not missing_fields:
                self.log_test("Themed Slot Result Structure", True)
                
                # Verify it's fortune_dragon theme
                if result.get('theme') == 'fortune_dragon':
                    self.log_test("Fortune Dragon Theme Correct", True)
                else:
                    self.log_test("Fortune Dragon Theme Correct", False, f"Expected fortune_dragon, got {result.get('theme')}")
                
                # Verify jackpot contribution
                expected_contribution = game_data['amount'] * 0.02
                actual_contribution = response.get('jackpot_contribution', 0)
                if abs(actual_contribution - expected_contribution) < 0.01:
                    self.log_test("Themed Slot Jackpot Contribution", True)
                else:
                    self.log_test("Themed Slot Jackpot Contribution", False, 
                                f"Expected ${expected_contribution:.2f}, got ${actual_contribution:.2f}")
                
                return True
            else:
                self.log_test("Themed Slot Result Structure", False, f"Missing fields: {missing_fields}")
                return False
        return False

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🎰 Starting NeonVegas Casino API Tests (Enhanced)")
        print("=" * 50)
        
        # Basic API tests
        self.test_root_endpoint()
        
        # Authentication tests
        if self.test_user_registration():
            self.test_user_login()
            self.test_get_user_profile()
        
        # Wallet tests
        self.test_wallet_balance()
        self.test_payid_deposit()
        self.test_payid_withdrawal()
        self.test_transaction_history()
        self.test_deposit_packages()
        self.test_stripe_checkout_creation()
        
        # PayID status test
        self.test_payid_status()
        
        # Jackpot tests
        self.test_jackpot_api()
        self.test_jackpot_winners()
        
        # Responsible gambling tests
        self.test_responsible_gambling_limits_get()
        self.test_responsible_gambling_limits_set()
        self.test_responsible_gambling_session()
        
        # Enhanced game tests
        self.test_enhanced_slots_game()
        self.test_blackjack_game()
        self.test_roulette_game()
        self.test_poker_game()
        self.test_game_history()
        
        # Leaderboard test
        self.test_leaderboard()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate < 50:
            print("❌ CRITICAL: More than 50% of tests failed!")
            return 1
        elif success_rate < 80:
            print("⚠️  WARNING: Some tests failed, needs attention")
            return 1
        else:
            print("✅ SUCCESS: Most tests passed!")
            return 0

def main():
    tester = NeonVegasCasinoTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())