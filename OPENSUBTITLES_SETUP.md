# OpenSubtitles.com API Setup Guide

This application uses the **OpenSubtitles.com REST API** for subtitle search and download.

## 🚀 Quick Start (5 minutes)

### Step 1: Create Account
1. Go to [OpenSubtitles.com Registration](https://www.opensubtitles.com/en/users/newuser)
2. Fill in username, password, and email
3. Verify your email address

### Step 2: Get API Key
1. Login to your OpenSubtitles account
2. Go to [Consumers Page](https://www.opensubtitles.com/en/consumers)
3. Click **"Create New Consumer"**
4. Fill in:
   - **App Name**: FUA Entertainment System (or any name)
   - **Description**: Personal video streaming app
   - **URL**: http://localhost:5000 (or your domain)
5. Click **"Create"**
6. **Copy the API Key** (it will only be shown once!)

### Step 3: Configure Application
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```env
   # REQUIRED - Your API Key from OpenSubtitles
   OPENSUBTITLES_API_KEY=YOUR_API_KEY_HERE
   
   # OPTIONAL - Improves rate limits (recommended)
   OPENSUBTITLES_USERNAME=your_username
   OPENSUBTITLES_PASSWORD=your_password
   ```

3. Save and restart the application:
   ```bash
   py run.py
   ```

---

## 📊 API Limits

### Free Tier (No Login)
- **Searches**: 40 per day
- **Downloads**: 200 per day
- **Rate Limit**: 1 request per second

### Free Tier (With Login)
- **Searches**: Unlimited
- **Downloads**: 200 per day
- **Rate Limit**: Higher limits
- ✅ **Recommended**: Login with username/password

### VIP Tier (Optional)
- **Downloads**: 1000 per day
- **Rate Limit**: Much higher
- **Cost**: ~$10/year
- **Details**: [OpenSubtitles VIP](https://www.opensubtitles.com/en/support)

---

## 🔧 Configuration Options

### Required Settings

```env
# Your API Key (REQUIRED)
OPENSUBTITLES_API_KEY=abc123xyz456...
```

### Optional Settings (Recommended)

```env
# Login for better rate limits
OPENSUBTITLES_USERNAME=your_username
OPENSUBTITLES_PASSWORD=your_password

# User Agent (required by API)
OPENSUBTITLES_USER_AGENT=FUA_Entertainment_System v1.0.0

# Search settings
SUBTITLE_SEARCH_TIMEOUT=30
SUBTITLE_HASH_SEARCH=true
SUBTITLE_MAX_RESULTS=20
```

---

## 🎯 How It Works

### 1. Hash-Based Search (Primary Method)
- **Most Accurate**: Matches exact video file
- Computes OpenSubtitles hash from video
- Finds subtitles for your specific release
- ✅ Recommended: Always enabled

### 2. Query Search (Fallback)
- Searches by filename or IMDB ID
- Used if hash search finds nothing
- Less accurate but broader results

### 3. Download
- Gets direct download link from API
- Downloads subtitle in SRT format
- Saves next to video file
- Auto-converts encoding if needed

---

## ✅ Testing Your Setup

### 1. Check API Key
After starting the app, watch the console for:
```
[OpenSubtitles] Successfully authenticated
```

If you see this, your API key and credentials are valid!

### 2. Search for Subtitles
1. Open any video in the player
2. Click **"Find Subtitles"** button
3. Select language (English/Arabic)
4. Click **"Search"**

### 3. Expected Behavior
**Console output:**
```
[OpenSubtitles] Searching by hash: abc123..., size: 1234567890
[OpenSubtitles] Found 15 subtitles by hash
```

**UI shows:**
- List of subtitle results
- Format: `OpenSubtitles - EN - Release.Name`
- Download buttons for each result

---

## 🐛 Troubleshooting

### Error: "OpenSubtitles API key not configured"
**Solution**: Set `OPENSUBTITLES_API_KEY` in `.env` file

### Error: "401 Unauthorized"
**Problem**: Invalid API key or expired
**Solution**: 
- Double-check API key in `.env`
- Generate new key at [Consumers Page](https://www.opensubtitles.com/en/consumers)

### Error: "429 Too Many Requests"
**Problem**: Rate limit exceeded
**Solution**:
- Add username/password to `.env` for better limits
- Wait a few hours
- Consider VIP upgrade

### Error: "No subtitles found"
**Problem**: Video not in OpenSubtitles database
**Solution**:
- Try different video quality/release
- Manually upload subtitle to OpenSubtitles
- Check IMDB ID and try searching with it

### Login Failed
**Problem**: Incorrect username/password
**Solution**:
- Verify credentials at [OpenSubtitles.com](https://www.opensubtitles.com)
- Can still use API without login (lower limits)

---

## 📝 API Key Best Practices

### ✅ DO:
- Keep API key secret (don't share publicly)
- Use `.env` file (not tracked by git)
- Rotate key if compromised
- Use username/password for better limits

### ❌ DON'T:
- Commit `.env` to git
- Share your API key
- Hardcode API key in code
- Use API key in public projects

---

## 🔗 Useful Links

- [OpenSubtitles.com](https://www.opensubtitles.com)
- [API Documentation](https://opensubtitles.stoplight.io/docs/opensubtitles-api/e3750fd63a100-getting-started)
- [Create Consumer (Get API Key)](https://www.opensubtitles.com/en/consumers)
- [VIP Subscription](https://www.opensubtitles.com/en/support)
- [Support Forum](https://forum.opensubtitles.org/)

---

## 📈 Upgrade to VIP (Optional)

If you hit rate limits or need more downloads:

**Benefits:**
- ✅ 1000 downloads/day (vs 200)
- ✅ Higher rate limits
- ✅ Priority support
- ✅ No ads
- ✅ Support the project

**Cost:** ~$10/year

**How to upgrade:**
1. Go to [OpenSubtitles VIP](https://www.opensubtitles.com/en/support)
2. Choose VIP subscription
3. Payment via PayPal/Card
4. API key automatically upgraded

---

## 🎉 You're All Set!

Your application is now configured to use OpenSubtitles.com API for subtitle search and download!

**Test it:**
1. Open a video
2. Click "Find Subtitles"
3. Search and download

Enjoy! 🍿
