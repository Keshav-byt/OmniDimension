from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import threading
import time
import json
import logging
import requests
import os
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)



# Configuration for OmniDimension webhooks
OMNIDIMENSION_WEBHOOK_URL = os.getenv('OMNIDIMENSION_WEBHOOK_URL', '')
OMNIDIMENSION_API_KEY = os.environ.get('OMNIDIMENSION_API_KEY')
if not OMNIDIMENSION_API_KEY:
    raise ValueError("OMNIDIMENSION_API_KEY environment variable is required")

# In-memory auction data with more realistic data
auction_data = {
    "products": {
        "prod_1": {
            "id": "prod_1",
            "name": "Vintage Rolex Submariner",
            "description": "Rare 1965 Rolex Submariner in excellent condition with original box and papers",
            "starting_price": 50000.00,
            "current_highest_bid": 55000.00,
            "highest_bidder": "user_001",
            "auction_end_time": datetime.now() + timedelta(minutes=30),
            "bidding_history": [
                {
                    "bid_id": "bid_001",
                    "bidder_id": "user_001",
                    "amount": 55000.00,
                    "timestamp": datetime.now() - timedelta(minutes=5)
                }
            ],
            "total_bids": 1,
            "status": "active",
            "category": "watches",
            "image_url": "https://awadwatches.com/wp-content/uploads/2019/03/1965_vintage_rolex_datejust_1601_rare_14k_gold_roman_dial_swiss_only_1.jpeg"
        },
        "prod_2": {
            "id": "prod_2",
            "name": "1967 Ford Mustang Fastback",
            "description": "Fully restored classic Mustang with 390 V8 engine, stunning condition",
            "starting_price": 25000000.00,
            "current_highest_bid": 28500000.00,
            "highest_bidder": "user_002",
            "auction_end_time": datetime.now() + timedelta(minutes=45),
            "bidding_history": [
                {
                    "bid_id": "bid_002",
                    "bidder_id": "user_002",
                    "amount": 26000000.00,
                    "timestamp": datetime.now() - timedelta(minutes=10)
                },
                {
                    "bid_id": "bid_003",
                    "bidder_id": "user_003",
                    "amount": 28500000.00,
                    "timestamp": datetime.now() - timedelta(minutes=3)
                }
            ],
            "total_bids": 2,
            "status": "active",
            "category": "vehicles",
            "image_url": "https://bringatrailer.com/wp-content/uploads/2019/05/1967_ford_mustang_fastback_1561126084a7ce40810bf523f006_exterior.jpg"
        },
        "prod_3": {
            "id": "prod_3",
            "name": "Original Van Gogh Sketch",
            "description": "Authenticated Van Gogh preparatory sketch with provenance documentation",
            "starting_price": 15000000.00,
            "current_highest_bid": 22000000.00,
            "highest_bidder": "user_004",
            "auction_end_time": datetime.now() + timedelta(minutes=20),
            "bidding_history": [
                {
                    "bid_id": "bid_004",
                    "bidder_id": "user_003",
                    "amount": 16000000.00,
                    "timestamp": datetime.now() - timedelta(minutes=15)
                },
                {
                    "bid_id": "bid_005", 
                    "bidder_id": "user_004",
                    "amount": 18500000.00,
                    "timestamp": datetime.now() - timedelta(minutes=12)
                },
                {
                    "bid_id": "bid_006",
                    "bidder_id": "user_005",
                    "amount": 22000000.00,
                    "timestamp": datetime.now() - timedelta(minutes=8)
                }
            ],
            "total_bids": 3,
            "status": "active",
            "category": "art",
            "image_url": "https://image.invaluable.com/housePhotos/Gallery320/16/665116/H19737-L198711707.jpg"
        }
    },
    "users": {
        "voice_user_001": {
            "id": "voice_user_001",
            "name": "Voice User",
            "phone": "+918439473928",
            "bidding_history": [],
            "total_spent": 0.0,
            "active_bids": []
        }
    }
}

# Global state for tracking active voice sessions
active_voice_sessions = {}

def send_omnidimension_webhook(session_id: str, message: str, data: dict = None):
    """Send webhook notification to OmniDimension for a specific session"""
    if not OMNIDIMENSION_WEBHOOK_URL:
        logger.warning("OmniDimension webhook URL not configured")
        return
    
    try:
        payload = {
            "session_id": session_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if OMNIDIMENSION_API_KEY:
            headers["Authorization"] = f"Bearer {OMNIDIMENSION_API_KEY}"
        
        response = requests.post(
            OMNIDIMENSION_WEBHOOK_URL,
            json=payload,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info(f"Webhook sent successfully to session {session_id}")
        else:
            logger.error(f"Webhook failed: Status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error sending webhook: {e}")

def check_auction_expiry():
    """Background thread to check and update expired auctions"""
    while True:
        try:
            current_time = datetime.now()
            for product_id, product in auction_data["products"].items():
                if product["status"] == "active" and current_time >= product["auction_end_time"]:
                    product["status"] = "ended"
                    logger.info(f"Auction for {product['name']} has ended! Winner: {product['highest_bidder']} with ${product['current_highest_bid']:.2f}")
                    
                    # Notify active voice sessions about auction end
                    notify_voice_sessions({
                        "type": "auction_ended",
                        "product_id": product_id,
                        "product_name": product["name"],
                        "final_amount": product["current_highest_bid"],
                        "winner": product["highest_bidder"]
                    })
            
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in auction expiry check: {e}")
            time.sleep(30)

def notify_voice_sessions(update_data):
    """Notify all active voice sessions about updates"""
    for session_id, session_data in active_voice_sessions.items():
        try:
            message = ""
            if update_data["type"] == "auction_ended":
                message = f"ATTENTION: The auction for {update_data['product_name']} has ended! Final winning bid: ${update_data['final_amount']:.2f}"
            elif update_data["type"] == "new_bid":
                message = f"NEW BID ALERT: ${update_data['amount']:.2f} placed on {update_data['product_name']}"
            elif update_data["type"] == "outbid":
                message = f"You have been outbid on {update_data['product_name']}! New highest bid: ${update_data['new_amount']:.2f}"
            
            send_omnidimension_webhook(session_id, message, update_data)
            
        except Exception as e:
            logger.error(f"Error notifying session {session_id}: {e}")

# Start background thread
threading.Thread(target=check_auction_expiry, daemon=True).start()

# ===== SESSION MANAGEMENT ENDPOINTS =====

@app.route('/api/session/start', methods=['POST'])
def start_voice_session():
    """Start a new voice session for a user"""
    try:
        data = request.json or {}
        phone_number = data.get('phone_number', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Create new bid
        new_bid = {
            "bid_id": str(uuid.uuid4()),
            "bidder_id": bidder_id,
            "amount": bid_amount,
            "timestamp": current_time
        }
        
        # Store previous highest bid info for notifications
        previous_highest_bid = product["current_highest_bid"]
        previous_highest_bidder = product["highest_bidder"]
        
        # Update product data
        product["current_highest_bid"] = bid_amount
        product["highest_bidder"] = bidder_id
        product["bidding_history"].append(new_bid)
        product["total_bids"] += 1
        
        # Update user data
        if bidder_id not in auction_data["users"]:
            auction_data["users"][bidder_id] = {
                "id": bidder_id,
                "name": f"User {bidder_id}",
                "bidding_history": [],
                "total_spent": 0.0,
                "active_bids": []
            }
        
        user = auction_data["users"][bidder_id]
        user["bidding_history"].append({
            "product_id": product_id,
            "product_name": product["name"],
            "amount": bid_amount,
            "timestamp": current_time.isoformat(),
            "status": "winning" if bidder_id == product["highest_bidder"] else "outbid"
        })
        
        # Add to active bids
        user["active_bids"] = [bid for bid in user["active_bids"] if bid["product_id"] != product_id]
        user["active_bids"].append({
            "product_id": product_id,
            "product_name": product["name"],
            "amount": bid_amount,
            "status": "winning"
        })
        
        # Update previous highest bidder status
        if previous_highest_bidder and previous_highest_bidder in auction_data["users"]:
            prev_user = auction_data["users"][previous_highest_bidder]
            for bid in prev_user["active_bids"]:
                if bid["product_id"] == product_id:
                    bid["status"] = "outbid"
        
        # Notify voice sessions about new bid
        notify_voice_sessions({
            "type": "new_bid",
            "product_id": product_id,
            "product_name": product["name"],
            "amount": bid_amount,
            "bidder_id": bidder_id,
            "previous_amount": previous_highest_bid
        })
        
        logger.info(f"New bid placed: ${bid_amount:.2f} on {product['name']} by {bidder_id}")
        
        return jsonify({
            "success": True,
            "message": f"Bid of ${bid_amount:.2f} placed successfully",
            "bid_details": {
                "bid_id": new_bid["bid_id"],
                "amount": bid_amount,
                "product_name": product["name"],
                "new_highest_bid": bid_amount,
                "previous_highest_bid": previous_highest_bid,
                "total_bids": product["total_bids"],
                "time_remaining": max(0, int((product["auction_end_time"] - current_time).total_seconds() / 60))
            }
        })
        
    except Exception as e:
        logger.error(f"Error placing bid: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/user/<user_id>/bids', methods=['GET'])
def get_user_bids(user_id):
    """Get all bids for a specific user"""
    try:
        if user_id not in auction_data["users"]:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        user = auction_data["users"][user_id]
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "bidding_history": user["bidding_history"],
            "active_bids": user["active_bids"],
            "total_bids": len(user["bidding_history"])
        })
    except Exception as e:
        logger.error(f"Error getting user bids: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ===== WEBHOOK ENDPOINTS FOR OMNIDIMENSION =====

@app.route('/api/webhook/omnidimension', methods=['POST'])
def omnidimension_webhook():
    """Receive webhooks from OmniDimension"""
    try:
        data = request.json
        logger.info(f"Received OmniDimension webhook: {data}")
        
        # Process the webhook data
        event_type = data.get("event_type", "")
        session_id = data.get("session_id", "")
        
        if event_type == "call_started" and session_id:
            # Auto-start session when call begins
            phone_number = data.get("caller_number", "")
            start_response = start_voice_session()
            logger.info(f"Auto-started session for call: {session_id}")
        
        elif event_type == "call_ended" and session_id:
            # Auto-end session when call ends
            if session_id in active_voice_sessions:
                active_voice_sessions.pop(session_id)
                logger.info(f"Auto-ended session for call: {session_id}")
        
        return jsonify({"success": True, "message": "Webhook processed"})
        
    except Exception as e:
        logger.error(f"Error processing OmniDimension webhook: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ===== HEALTH CHECK AND STATUS ENDPOINTS =====

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        current_time = datetime.now()
        active_auctions = len([p for p in auction_data["products"].values() if p["status"] == "active"])
        
        return jsonify({
            "status": "healthy",
            "timestamp": current_time.isoformat(),
            "active_sessions": len(active_voice_sessions),
            "active_auctions": active_auctions,
            "total_users": len(auction_data["users"])
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_system_status():
    """Get detailed system status"""
    try:
        current_time = datetime.now()
        
        # Calculate auction statistics
        total_auctions = len(auction_data["products"])
        active_auctions = len([p for p in auction_data["products"].values() if p["status"] == "active"])
        ended_auctions = total_auctions - active_auctions
        
        # Calculate bidding statistics
        total_bids = sum(p["total_bids"] for p in auction_data["products"].values())
        total_bid_value = sum(p["current_highest_bid"] for p in auction_data["products"].values())
        
        # Session statistics
        active_sessions_count = len(active_voice_sessions)
        
        return jsonify({
            "success": True,
            "timestamp": current_time.isoformat(),
            "auction_stats": {
                "total_auctions": total_auctions,
                "active_auctions": active_auctions,
                "ended_auctions": ended_auctions,
                "total_bids": total_bids,
                "total_bid_value": total_bid_value
            },
            "session_stats": {
                "active_sessions": active_sessions_count,
                "total_users": len(auction_data["users"])
            },
            "system_config": {
                "webhook_configured": bool(OMNIDIMENSION_WEBHOOK_URL),
                "api_key_configured": bool(OMNIDIMENSION_API_KEY)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':    
    app.run(debug=True, host='0.0.0.0', port=5000) or get user based on phone number
        user_id = f"voice_user_{phone_number.replace('+', '').replace('-', '')}" if phone_number else f"voice_user_{session_id}"
        
        if user_id not in auction_data["users"]:
            auction_data["users"][user_id] = {
                "id": user_id,
                "name": f"Voice User ({phone_number})" if phone_number else f"Voice User {session_id[:8]}",
                "phone": phone_number,
                "bidding_history": [],
                "total_spent": 0.0,
                "active_bids": []
            }
        
        # Store session info
        active_voice_sessions[session_id] = {
            "user_id": user_id,
            "phone_number": phone_number,
            "start_time": datetime.now(),
            "last_activity": datetime.now()
        }
        
        logger.info(f"Started voice session {session_id} for user {user_id}")
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "user_id": user_id,
            "message": "Voice session started successfully"
        })
        
    except Exception as e:
        logger.error(f"Error starting voice session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/session/<session_id>/end', methods=['POST'])
def end_voice_session(session_id):
    """End a voice session"""
    try:
        if session_id in active_voice_sessions:
            session_data = active_voice_sessions.pop(session_id)
            logger.info(f"Ended voice session {session_id}")
            
            return jsonify({
                "success": True,
                "message": "Voice session ended successfully",
                "session_duration": str(datetime.now() - session_data["start_time"])
            })
        else:
            return jsonify({"success": False, "error": "Session not found"}), 404
            
    except Exception as e:
        logger.error(f"Error ending voice session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ===== VOICE-OPTIMIZED AUCTION ENDPOINTS =====

@app.route('/api/voice/auctions/summary', methods=['GET'])
def get_voice_auction_summary():
    """Get a voice-friendly summary of all active auctions"""
    try:
        current_time = datetime.now()
        active_auctions = []
        
        for product_id, product in auction_data["products"].items():
            if product["status"] == "active" and current_time < product["auction_end_time"]:
                time_remaining = product["auction_end_time"] - current_time
                minutes_remaining = max(0, int(time_remaining.total_seconds() / 60))
                
                active_auctions.append({
                    "id": product_id,
                    "name": product["name"],
                    "current_bid": product["current_highest_bid"],
                    "minutes_remaining": minutes_remaining,
                    "total_bids": product["total_bids"],
                    "voice_description": f"{product['name']} - Current bid: ${product['current_highest_bid']:.0f} - {minutes_remaining} minutes remaining"
                })
        
        # Sort by urgency (time remaining)
        active_auctions.sort(key=lambda x: x["minutes_remaining"])
        
        summary_text = f"There are {len(active_auctions)} active auctions. "
        if active_auctions:
            summary_text += "Here are the current items: "
            for i, auction in enumerate(active_auctions[:3], 1):  # Limit to top 3 for voice
                summary_text += f"{i}. {auction['voice_description']}. "
        
        return jsonify({
            "success": True,
            "total_active": len(active_auctions),
            "auctions": active_auctions,
            "voice_summary": summary_text.strip()
        })
        
    except Exception as e:
        logger.error(f"Error getting voice auction summary: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/voice/auctions/<product_id>/details', methods=['GET'])
def get_voice_auction_details(product_id):
    """Get voice-friendly details for a specific auction"""
    try:
        if product_id not in auction_data["products"]:
            return jsonify({
                "success": False, 
                "error": "Product not found",
                "voice_message": "Sorry, I couldn't find that auction item."
            }), 404
        
        product = auction_data["products"][product_id]
        current_time = datetime.now()
        time_remaining = product["auction_end_time"] - current_time
        
        if time_remaining.total_seconds() <= 0 or product["status"] != "active":
            return jsonify({
                "success": False,
                "error": "Auction has ended",
                "voice_message": f"The auction for {product['name']} has already ended."
            }), 400
        
        minutes_remaining = max(0, int(time_remaining.total_seconds() / 60))
        seconds_remaining = max(0, int(time_remaining.total_seconds() % 60))
        
        voice_details = f"Here are the details for {product['name']}. "
        voice_details += f"Description: {product['description']}. "
        voice_details += f"Current highest bid is ${product['current_highest_bid']:.0f}. "
        voice_details += f"There have been {product['total_bids']} bids so far. "
        voice_details += f"Time remaining: {minutes_remaining} minutes and {seconds_remaining} seconds. "
        voice_details += f"Minimum next bid would be ${product['current_highest_bid'] + 50:.0f}."
        
        return jsonify({
            "success": True,
            "product": {
                "id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "current_highest_bid": product["current_highest_bid"],
                "total_bids": product["total_bids"],
                "minutes_remaining": minutes_remaining,
                "seconds_remaining": seconds_remaining,
                "minimum_next_bid": product["current_highest_bid"] + 50,
                "status": product["status"]
            },
            "voice_details": voice_details
        })
        
    except Exception as e:
        logger.error(f"Error getting voice auction details: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/voice/bid', methods=['POST'])
def place_voice_bid():
    """Place a bid from voice agent with session context"""
    try:
        data = request.json
        required_fields = ["product_id", "amount", "session_id"]
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing {field}",
                    "voice_message": "I need the product ID, bid amount, and session information to place your bid."
                }), 400
        
        product_id = data["product_id"]
        session_id = data["session_id"]
        
        # Get user from session
        if session_id not in active_voice_sessions:
            return jsonify({
                "success": False,
                "error": "Invalid session",
                "voice_message": "Your session has expired. Please start a new call."
            }), 400
        
        session_data = active_voice_sessions[session_id]
        bidder_id = session_data["user_id"]
        
        # Update last activity
        session_data["last_activity"] = datetime.now()
        
        if product_id not in auction_data["products"]:
            return jsonify({
                "success": False,
                "error": "Product not found",
                "voice_message": "I couldn't find that auction item. Please try again."
            }), 404
        
        product = auction_data["products"][product_id]
        
        try:
            bid_amount = float(data["amount"])
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Invalid bid amount",
                "voice_message": "Please provide a valid dollar amount for your bid."
            }), 400
        
        # Check if auction is still active
        current_time = datetime.now()
        if current_time >= product["auction_end_time"] or product["status"] != "active":
            return jsonify({
                "success": False,
                "error": "Auction has ended",
                "voice_message": f"Sorry, the auction for {product['name']} has already ended."
            }), 400
        
        # Check if bid is higher than current highest bid
        minimum_bid = product["current_highest_bid"] + 50.00
        if bid_amount <= product["current_highest_bid"]:
            return jsonify({
                "success": False,
                "error": "Bid too low",
                "voice_message": f"Your bid must be higher than the current bid of ${product['current_highest_bid']:.0f}. The minimum bid is ${minimum_bid:.0f}."
            }), 400
        
        if bid_amount < minimum_bid:
            return jsonify({
                "success": False,
                "error": "Bid increment too small",
                "voice_message": f"Your bid must be at least ${minimum_bid:.0f}, which includes the 50 dollar minimum increment."
            }), 400
        
        # Create new bid
        new_bid = {
            "bid_id": str(uuid.uuid4()),
            "bidder_id": bidder_id,
            "amount": bid_amount,
            "timestamp": current_time
        }
        
        # Store previous info for notifications
        previous_highest_bid = product["current_highest_bid"]
        previous_highest_bidder = product["highest_bidder"]
        
        # Update product data
        product["current_highest_bid"] = bid_amount
        product["highest_bidder"] = bidder_id
        product["bidding_history"].append(new_bid)
        product["total_bids"] += 1
        
        # Update user data
        user = auction_data["users"][bidder_id]
        user["bidding_history"].append({
            "product_id": product_id,
            "product_name": product["name"],
            "amount": bid_amount,
            "timestamp": current_time.isoformat(),
            "status": "winning"
        })
        
        # Update active bids
        user["active_bids"] = [bid for bid in user["active_bids"] if bid["product_id"] != product_id]
        user["active_bids"].append({
            "product_id": product_id,
            "product_name": product["name"],
            "amount": bid_amount,
            "status": "winning"
        })
        
        # Notify previous highest bidder they've been outbid
        if previous_highest_bidder and previous_highest_bidder != bidder_id:
            if previous_highest_bidder in auction_data["users"]:
                prev_user = auction_data["users"][previous_highest_bidder]
                for bid in prev_user["active_bids"]:
                    if bid["product_id"] == product_id:
                        bid["status"] = "outbid"
            
            # Send outbid notification
            notify_voice_sessions({
                "type": "outbid",
                "product_id": product_id,
                "product_name": product["name"],
                "new_amount": bid_amount,
                "previous_bidder": previous_highest_bidder
            })
        
        # Notify all sessions about new bid
        notify_voice_sessions({
            "type": "new_bid",
            "product_id": product_id,
            "product_name": product["name"],
            "amount": bid_amount,
            "bidder_id": bidder_id,
            "previous_amount": previous_highest_bid
        })
        
        logger.info(f"Voice bid placed: ${bid_amount:.2f} on {product['name']} by {bidder_id} (session: {session_id})")
        
        time_remaining = max(0, int((product["auction_end_time"] - current_time).total_seconds() / 60))
        
        success_message = f"Congratulations! Your bid of ${bid_amount:.0f} on {product['name']} has been placed successfully. "
        success_message += f"You are now the highest bidder. There are {time_remaining} minutes remaining in this auction."
        
        return jsonify({
            "success": True,
            "voice_message": success_message,
            "bid_details": {
                "bid_id": new_bid["bid_id"],
                "amount": bid_amount,
                "product_name": product["name"],
                "new_highest_bid": bid_amount,
                "previous_highest_bid": previous_highest_bid,
                "total_bids": product["total_bids"],
                "minutes_remaining": time_remaining
            }
        })
        
    except Exception as e:
        logger.error(f"Error placing voice bid: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "voice_message": "I'm sorry, there was an error processing your bid. Please try again."
        }), 500

@app.route('/api/voice/user/status', methods=['POST'])
def get_voice_user_status():
    """Get user's current bidding status for voice"""
    try:
        data = request.json or {}
        session_id = data.get("session_id")
        
        if not session_id or session_id not in active_voice_sessions:
            return jsonify({
                "success": False,
                "error": "Invalid session",
                "voice_message": "Your session has expired. Please start a new call."
            }), 400
        
        session_data = active_voice_sessions[session_id]
        user_id = session_data["user_id"]
        user = auction_data["users"][user_id]
        
        active_bids = user["active_bids"]
        winning_bids = [bid for bid in active_bids if bid["status"] == "winning"]
        outbid_bids = [bid for bid in active_bids if bid["status"] == "outbid"]
        
        status_message = f"Here's your current status: "
        
        if not active_bids:
            status_message += "You don't have any active bids at the moment."
        else:
            if winning_bids:
                status_message += f"You are currently winning {len(winning_bids)} auction"
                if len(winning_bids) > 1:
                    status_message += "s"
                status_message += ": "
                for bid in winning_bids:
                    status_message += f"{bid['product_name']} with a bid of ${bid['amount']:.0f}. "
            
            if outbid_bids:
                status_message += f"You have been outbid on {len(outbid_bids)} item"
                if len(outbid_bids) > 1:
                    status_message += "s"
                status_message += ": "
                for bid in outbid_bids:
                    status_message += f"{bid['product_name']}. "
        
        return jsonify({
            "success": True,
            "voice_message": status_message.strip(),
            "user_status": {
                "total_active_bids": len(active_bids),
                "winning_bids": len(winning_bids),
                "outbid_bids": len(outbid_bids),
                "total_bid_history": len(user["bidding_history"])
            },
            "active_bids": active_bids
        })
        
    except Exception as e:
        logger.error(f"Error getting voice user status: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "voice_message": "I'm sorry, I couldn't retrieve your status right now."
        }), 500

# ===== ORIGINAL ENDPOINTS (kept for compatibility) =====

@app.route('/api/auctions', methods=['GET'])
def get_all_auctions():
    """Get all auction products with current status"""
    try:
        products_with_time = {}
        current_time = datetime.now()
        
        for product_id, product in auction_data["products"].items():
            product_copy = product.copy()
            time_remaining = product["auction_end_time"] - current_time
            
            if time_remaining.total_seconds() > 0 and product["status"] == "active":
                minutes_remaining = max(0, int(time_remaining.total_seconds() / 60))
                seconds_remaining = max(0, int(time_remaining.total_seconds() % 60))
                product_copy["time_remaining_minutes"] = minutes_remaining
                product_copy["time_remaining_seconds"] = seconds_remaining
                product_copy["time_remaining_text"] = f"{minutes_remaining} minutes and {seconds_remaining} seconds"
                if minutes_remaining < 5:
                    product_copy["urgency"] = "high"
                elif minutes_remaining < 15:
                    product_copy["urgency"] = "medium"
                else:
                    product_copy["urgency"] = "low"
            else:
                product_copy["time_remaining_minutes"] = 0
                product_copy["time_remaining_seconds"] = 0
                product_copy["time_remaining_text"] = "Auction ended"
                product_copy["status"] = "ended"
                product_copy["urgency"] = "none"
            
            # Convert datetime objects to strings for JSON serialization
            product_copy["auction_end_time"] = product["auction_end_time"].isoformat()
            bidding_history_copy = []
            for bid in product_copy["bidding_history"]:
                bid_copy = bid.copy()
                bid_copy["timestamp"] = bid["timestamp"].isoformat()
                bidding_history_copy.append(bid_copy)
            product_copy["bidding_history"] = bidding_history_copy
            
            products_with_time[product_id] = product_copy
        
        return jsonify({
            "success": True,
            "products": products_with_time,
            "total_products": len(products_with_time),
            "active_products": len([p for p in products_with_time.values() if p["status"] == "active"])
        })
    except Exception as e:
        logger.error(f"Error getting auctions: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auctions/<product_id>', methods=['GET'])
def get_auction_details(product_id):
    """Get details for a specific auction product"""
    try:
        if product_id not in auction_data["products"]:
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        product = auction_data["products"][product_id].copy()
        current_time = datetime.now()
        time_remaining = product["auction_end_time"] - current_time
        
        if time_remaining.total_seconds() > 0 and product["status"] == "active":
            minutes_remaining = max(0, int(time_remaining.total_seconds() / 60))
            seconds_remaining = max(0, int(time_remaining.total_seconds() % 60))
            product["time_remaining_minutes"] = minutes_remaining
            product["time_remaining_seconds"] = seconds_remaining
            product["time_remaining_text"] = f"{minutes_remaining} minutes and {seconds_remaining} seconds"
        else:
            product["time_remaining_minutes"] = 0
            product["time_remaining_seconds"] = 0
            product["time_remaining_text"] = "Auction ended"
            if product["status"] == "active":
                product["status"] = "ended"
        
        # Convert datetime objects to strings
        product["auction_end_time"] = product["auction_end_time"].isoformat()
        bidding_history_copy = []
        for bid in product["bidding_history"]:
            bid_copy = bid.copy()
            bid_copy["timestamp"] = bid["timestamp"].isoformat()
            bidding_history_copy.append(bid_copy)
        product["bidding_history"] = bidding_history_copy
        
        return jsonify({
            "success": True,
            "product": product
        })
    except Exception as e:
        logger.error(f"Error getting auction details: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auctions/<product_id>/bid', methods=['POST'])
def place_bid(product_id):
    """Place a new bid on a product (original endpoint)"""
    try:
        if product_id not in auction_data["products"]:
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        data = request.json
        if not data or "amount" not in data or "bidder_id" not in data:
            return jsonify({"success": False, "error": "Missing bid amount or bidder ID"}), 400
        
        product = auction_data["products"][product_id]
        try:
            bid_amount = float(data["amount"])
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid bid amount"}), 400
            
        bidder_id = data["bidder_id"]
        
        # Check if auction is still active
        current_time = datetime.now()
        if current_time >= product["auction_end_time"] or product["status"] != "active":
            return jsonify({"success": False, "error": "Auction has ended"}), 400
        
        # Check if bid is higher than current highest bid
        minimum_bid = product["current_highest_bid"] + 50.00  # Minimum increment
        if bid_amount <= product["current_highest_bid"]:
            return jsonify({
                "success": False,
                "error": f"Bid must be higher than current highest bid of ${product['current_highest_bid']:.2f}. Minimum bid: ${minimum_bid:.2f}"
            }), 400
        
        if bid_amount < minimum_bid:
            return jsonify({
                "success": False,
                "error": f"Bid must be at least ${minimum_bid:.2f} (current bid + $50 minimum increment)"
            }), 400
        
        # Create
