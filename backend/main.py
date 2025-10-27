"""
Real-time Price Monitor Backend using FastAPI and DataBento Live API
"""

import asyncio
import os
from typing import AsyncGenerator
import databento as db
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
# Get the directory where this script is located
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="Real-time Price Monitor")

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABENTO_API_KEY = os.getenv("DATABENTO_API_KEY")
DATASET = "GLBX.MDP3"  # Example: CME Globex
SCHEMA = "mbp-1"  # Market by Price (Level 1)

# Validate API key
if not DATABENTO_API_KEY or DATABENTO_API_KEY == "your-api-key-here":
    print("⚠️  WARNING: DATABENTO_API_KEY environment variable not set!")
    print("📝 Please set DATABENTO_API_KEY environment variable")
    print("💡 Example: export DATABENTO_API_KEY='your-api-key'")
else:
    # Print partial API key for verification (security best practice)
    masked_key = f"{DATABENTO_API_KEY[:8]}...{DATABENTO_API_KEY[-4:]}" if len(DATABENTO_API_KEY) > 12 else "***"
    print(f"✅ API Key loaded: {masked_key}")
    print(f"📊 Dataset: {DATASET}")
    print(f"📋 Schema: {SCHEMA}")

# Test DataBento import and basic functionality
try:
    print(f"🔍 DataBento version: {db.__version__}")
    print(f"🔍 DataBento Live class: {db.Live}")
    print(f"🔍 Live class methods: {[method for method in dir(db.Live) if not method.startswith('_')]}")
except Exception as e:
    print(f"❌ DataBento import issue: {e}")


async def stream_price_data(symbols: list[str]) -> AsyncGenerator[str, None]:
    """
    Stream real-time price data from DataBento Live API

    Args:
        symbols: List of symbols to subscribe to (e.g., ['ES.FUT', 'NQ.FUT'])
    """
    try:
        # Check if API key is available
        if not DATABENTO_API_KEY:
            error_data = {
                "error": "DATABENTO_API_KEY environment variable not set",
                "details": "Please set DATABENTO_API_KEY environment variable to use the live data stream",
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            return
        
        print(f"📊 Dataset: {DATASET}")
        print(f"📋 Schema: {SCHEMA}")
        print(f"🎯 Symbols: {symbols}")
        
        # Initialize DataBento Live client
        client = db.Live(key=DATABENTO_API_KEY)
        print("✅ DataBento client initialized")
        
        # Subscribe to symbols with proper parameters (synchronous)
        print("🔄 Subscribing to symbols...")
        client.subscribe(
            dataset=DATASET,
            schema=SCHEMA,
            symbols=symbols,
            stype_in="raw_symbol"
        )
        print(f"✅ Successfully subscribed to symbols: {symbols}")

        print("🔄 Starting data stream...")
        
        # Send initial status message
        status_data = {
            "status": "connected",
            "message": "Connected to DataBento, waiting for price data...",
            "symbols": symbols,
            "timestamp": datetime.now().isoformat()
        }
        print(f"📤 Sending status message: {status_data}")
        yield f"data: {json.dumps(status_data)}\n\n"
        
        # Send a test message to verify SSE is working
        test_data = {
            "test": "SSE connection working",
            "timestamp": datetime.now().isoformat()
        }
        print(f"🧪 Sending test message: {test_data}")
        yield f"data: {json.dumps(test_data)}\n\n"
        
        # Stream data with proper error handling
        try:
            async for record in client:
                try:
                    # Debug: Print raw record to understand structure
                    print(f"📦 Received record: {type(record)} - {record}")
                    
                    # Handle different record types
                    record_type = type(record).__name__
                    
                    if record_type == "SymbolMappingMsg":
                        # Handle symbol mapping messages
                        print(f"🗺️ Symbol mapping: {getattr(record, 'stype_in_symbol', 'Unknown')} -> {getattr(record, 'stype_out_symbol', 'Unknown')}")
                        continue  # Skip symbol mapping messages for price display
                    
                    elif record_type in ["MBP1Msg", "MBPMsg", "TradeMsg"]:
                        # Handle actual price/trade data
                        # Extract data from MBP1Msg structure
                        # Get symbol - try different possible fields
                        symbol = getattr(record, 'symbol', getattr(record, 'instrument_id', 'UNKNOWN'))
                        timestamp = getattr(record, 'ts_event', getattr(record.hd, 'ts_event', datetime.now()))
                        
                        # Extract bid/ask data from levels array
                        bid_price = None
                        ask_price = None
                        bid_size = None
                        ask_size = None
                        
                        if hasattr(record, 'levels') and record.levels and len(record.levels) > 0:
                            level = record.levels[0]
                            
                            # Extract prices - they may be in fixed-point format (int * 1e9)
                            # If the value is > 1000000, it's likely in fixed-point format, divide by 1e9
                            raw_bid = level.bid_px if hasattr(level, 'bid_px') else None
                            raw_ask = level.ask_px if hasattr(level, 'ask_px') else None
                            
                            # Convert to float, then check if we need to scale down
                            if raw_bid is not None:
                                bid_value = float(raw_bid)
                                # Check if value seems to be in fixed-point format (very large number)
                                if bid_value > 1000000:
                                    bid_price = bid_value / 1e9
                                else:
                                    bid_price = bid_value
                            else:
                                bid_price = None
                            
                            if raw_ask is not None:
                                ask_value = float(raw_ask)
                                # Check if value seems to be in fixed-point format (very large number)
                                if ask_value > 1000000:
                                    ask_price = ask_value / 1e9
                                else:
                                    ask_price = ask_value
                            else:
                                ask_price = None
                            
                            bid_size = int(level.bid_sz) if hasattr(level, 'bid_sz') and level.bid_sz else None
                            ask_size = int(level.ask_sz) if hasattr(level, 'ask_sz') and level.ask_sz else None
                        
                        data = {
                            "symbol": str(symbol),
                            "timestamp": str(timestamp),
                            "bid_price": bid_price,
                            "ask_price": ask_price,
                            "bid_size": bid_size,
                            "ask_size": ask_size,
                            "received_at": datetime.now().isoformat(),
                            "record_type": record_type
                        }

                        # Always send data to frontend (even if price data is None)
                        print(f"💰 Sending {record_type} data: {data['symbol']} - Bid: {data['bid_price']}, Ask: {data['ask_price']}")
                        yield f"data: {json.dumps(data)}\n\n"
                    
                    else:
                        # Handle other record types
                        print(f"ℹ️ Unhandled record type: {record_type}")
                        continue
                        
                except Exception as record_error:
                    print(f"❌ Error processing record: {record_error}")
                    error_data = {
                        "error": f"Record processing error: {str(record_error)}",
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    
        except Exception as iteration_error:
            print(f"❌ Error during iteration: {iteration_error}")
            error_data = {
                "error": f"Iteration error: {str(iteration_error)}",
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    except Exception as e:
        error_msg = str(e)
        print(f"❌ DataBento connection error: {error_msg}")
        
        # Provide specific guidance for authentication errors
        if "authentication failed" in error_msg.lower() or "cram" in error_msg.lower():
            detailed_error = {
                "error": "DataBento Authentication Failed",
                "details": "Invalid API key or insufficient permissions for live data",
                "solutions": [
                    "Verify your API key is correct",
                    "Ensure your key has live data access permissions", 
                    "Check if your key is for live data (not just historical)",
                    "Contact DataBento support if key appears valid"
                ],
                "timestamp": datetime.now().isoformat()
            }
        elif "nonetype" in error_msg.lower() or "await" in error_msg.lower():
            detailed_error = {
                "error": "DataBento Client Initialization Failed",
                "details": "Client object is None, likely due to subscription failure",
                "solutions": [
                    "Check if your API key has live data permissions",
                    "Verify the dataset and schema are correct",
                    "Ensure symbols are valid for the dataset",
                    "Check DataBento service status"
                ],
                "timestamp": datetime.now().isoformat()
            }
        else:
            detailed_error = {
                "error": f"DataBento API error: {error_msg}",
                "timestamp": datetime.now().isoformat()
            }
            
        yield f"data: {json.dumps(detailed_error)}\n\n"
    finally:
        print("🧹 DataBento connection cleanup completed")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Real-time Price Monitor",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/test-client")
async def test_client_creation():
    """Test basic DataBento client creation"""
    if not DATABENTO_API_KEY:
        return {
            "status": "error",
            "message": "DATABENTO_API_KEY environment variable not set",
            "error_type": "ConfigurationError"
        }
    
    try:
        client = db.Live(key=DATABENTO_API_KEY)
        return {
            "status": "success",
            "message": "Client created successfully",
            "client_type": str(type(client)),
            "client_id": id(client),
            "has_subscribe": hasattr(client, 'subscribe'),
            "methods": [method for method in dir(client) if not method.startswith('_')]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Client creation failed: {str(e)}",
            "error_type": str(type(e))
        }


@app.get("/stream/prices")
async def stream_prices(symbols: str = "ES.FUT,NQ.FUT"):
    """
    SSE endpoint to stream real-time prices

    Query Parameters:
        symbols: Comma-separated list of symbols (e.g., "ES.FUT,NQ.FUT")

    Returns:
        Server-Sent Events stream with real-time price data
    """
    symbol_list = [s.strip() for s in symbols.split(",")]

    if not symbol_list:
        raise HTTPException(status_code=400, detail="At least one symbol is required")

    return StreamingResponse(
        stream_price_data(symbol_list),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.get("/symbols")
async def get_available_symbols():
    """Get list of commonly traded symbols"""
    return {
        "futures": [
            {"symbol": "ES.FUT", "name": "E-mini S&P 500"},
            {"symbol": "NQ.FUT", "name": "E-mini NASDAQ-100"},
            {"symbol": "YM.FUT", "name": "E-mini Dow Jones"},
            {"symbol": "RTY.FUT", "name": "E-mini Russell 2000"},
            {"symbol": "GC.FUT", "name": "Gold Futures"},
            {"symbol": "CL.FUT", "name": "Crude Oil Futures"},
        ]
    }


@app.get("/test-connection")
async def test_databento_connection():
    """Test DataBento API connection"""
    if not DATABENTO_API_KEY:
        return {
            "status": "error",
            "message": "DATABENTO_API_KEY environment variable not set. Please set DATABENTO_API_KEY environment variable.",
            "api_key_set": False,
            "dataset": DATASET,
            "schema": SCHEMA,
            "error_type": "ConfigurationError"
        }
    
    try:
        # Test basic client initialization
        client = db.Live(key=DATABENTO_API_KEY)
        print(f"✅ Client created: {type(client)}")
        print(f"🔍 Client attributes: {dir(client)}")
        
        # Check if subscribe method exists and is callable
        if hasattr(client, 'subscribe'):
            print("✅ Subscribe method exists")
            print(f"🔍 Subscribe method: {client.subscribe}")
        else:
            print("❌ Subscribe method not found")
            return {
                "status": "error",
                "message": "Subscribe method not found on client",
                "client_methods": [method for method in dir(client) if not method.startswith('_')]
            }
        
        # Test subscription with error handling (without await)
        print("🔄 Testing subscription...")
        try:
            result = client.subscribe(
                dataset=DATASET,
                schema=SCHEMA,
                symbols=["ES.FUT"],
                stype_in="parent"
            )
            print(f"✅ Subscription result: {result}")
            print(f"🔍 Result type: {type(result)}")
            
            return {
                "status": "success",
                "message": "DataBento client and subscription test successful",
                "api_key_set": DATABENTO_API_KEY != "your-api-key-here",
                "dataset": DATASET,
                "schema": SCHEMA,
                "client_type": str(type(client)),
                "subscription_result": str(result)
            }
        except Exception as sub_error:
            print(f"❌ Subscription failed: {sub_error}")
            return {
                "status": "error",
                "message": f"Subscription failed: {str(sub_error)}",
                "api_key_set": DATABENTO_API_KEY != "your-api-key-here",
                "dataset": DATASET,
                "schema": SCHEMA,
                "error_type": str(type(sub_error))
            }
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return {
            "status": "error",
            "message": f"DataBento test failed: {str(e)}",
            "api_key_set": DATABENTO_API_KEY != "your-api-key-here",
            "dataset": DATASET,
            "schema": SCHEMA,
            "error_type": str(type(e))
        }


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
