# PolicyAgentX Setup & API Connection Guide

## Frontend API Connection Fixed ✅

### What Was Wrong
- Frontend was receiving HTML instead of JSON (403/500 errors)
- Issue: API endpoint resolution and error handling

### What's Fixed

#### 1. **Environment Variables** ([frontend/.env.local](frontend/.env.local))
```
VITE_API_URL=http://localhost:5000
```

#### 2. **API Service** ([frontend/src/lib/api.ts](frontend/src/lib/api.ts))
- Uses full backend URL: `http://localhost:5000`
- NOT relative paths like `/api`
- Defensive JSON parsing with error logging
- Proper Content-Type headers
- Handles both connection and JSON errors

#### 3. **Error Handling** ([frontend/src/pages/SimulatePolicy.tsx](frontend/src/pages/SimulatePolicy.tsx))
- Checks if backend is running
- Logs errors to console
- Displays user-friendly error messages
- Distinguishes between connection, parsing, and API errors

#### 4. **Backend CORS** ([backend/run.py](backend/run.py))
- Simplified CORS configuration
- Allows requests from localhost:8080 and localhost:3000
- Supports GET, POST, OPTIONS methods
- Content-Type header explicitly allowed

## Setup Instructions

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python run.py
# Output: Starting PolicyAgentX Backend on http://0.0.0.0:5000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Output: Frontend running on http://localhost:8080
```

### 3. Verify Connection
- Frontend: http://localhost:8080
- Backend: http://localhost:5000
- Check browser console for API logs
- Backend terminal shows error details

## Testing The Fix

1. Open frontend in browser
2. Go to "Simulate Policy" page
3. Send test message: "increase fuel prices by 5% in india"
4. Check browser console (F12) for API logs
5. If error: Check backend terminal for detailed error

## Key Files Modified

| File | Change |
|------|--------|
| frontend/src/lib/api.ts | Full URL + defensive parsing |
| frontend/src/pages/SimulatePolicy.tsx | Better error messages |
| frontend/.env.local | Backend URL config |
| backend/run.py | Enhanced CORS + error handlers |
| frontend/vite.config.ts | Removed proxy (using full URLs) |

## If Still Getting HTML Response

### 1. Backend Not Running?
```
Backend connection failed. Is the Flask server running on http://localhost:5000?
```
**Fix:** Start backend with `python run.py`

### 2. Agent Error (Gemini API)?
Check backend console for:
- GEMINI_API_KEY errors
- Agent execution errors

**Fix:** Verify .env has API key: `cat backend/.env`

### 3. MongoDB Connection?
Check backend console for MongoDB errors

**Fix:** Start MongoDB or ensure service is running

## Debugging Workflow

1. **Frontend Console (F12)**: Shows API request/response details
2. **Backend Terminal**: Shows server errors and full stack traces
3. **Network Tab (F12)**: Inspect actual HTTP requests/responses

## Environment Files

- **backend/.env** - GEMINI_API_KEY
- **frontend/.env.local** - VITE_API_URL (not in git)
- **frontend/.env.example** - Template for developers
