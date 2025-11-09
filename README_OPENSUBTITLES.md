
---

## ⚡ Quick Start (3 Steps)

### 1️⃣ Get Your API Key
1. Register at https://www.opensubtitles.com/en/users/newuser
2. Get API key at https://www.opensubtitles.com/en/consumers
3. Copy the API key (shown only once!)

### 2️⃣ Configure
```bash
copy .env.example .env
```

Edit `.env` and add your API key:
```env
OPENSUBTITLES_API_KEY=YOUR_API_KEY_HERE
```

### 3️⃣ Run
```bash
pip install -r requirements.txt
py run.py
```

**Done!** 🎉

---

## 📚 Documentation

- **[Setup Guide](OPENSUBTITLES_SETUP.md)** - Complete setup instructions
- **[Implementation Details](IMPLEMENTATION_SUMMARY.md)** - Technical changes
- **[Configuration](CONFIG.md)** - All config options
- **[.env Example](.env.example)** - Environment template

---

## ✨ Key Features

✅ **More Reliable** - Official API vs outdated library  
✅ **Consistent Results** - No more "sometimes works, sometimes doesn't"  
✅ **Cleaner Code** - Removed subliminal + babelfish dependencies  
✅ **Better Errors** - Clear API error messages  
✅ **Free Tier** - 200 downloads/day, unlimited searches (with login)  

---

## 🔑 API Configuration

### Required:
```env
OPENSUBTITLES_API_KEY=your_key_here
```

### Optional (Recommended for better rate limits):
```env
OPENSUBTITLES_USERNAME=your_username
OPENSUBTITLES_PASSWORD=your_password
```

---

## 🎯 How It Works

1. **Hash-Based Search** (Primary)
   - Computes video file hash
   - Finds exact subtitle match
   - Most accurate method

2. **Query Search** (Fallback)
   - Searches by filename/IMDB
   - Used if hash search fails
   - Broader results

3. **Download**
   - Gets download link from API
   - Downloads subtitle as SRT
   - Saves next to video file

---

## 📊 API Limits (Free Tier)

| Limit | Without Login | With Login |
|-------|--------------|------------|
| **Searches** | 40/day | Unlimited |
| **Downloads** | 200/day | 200/day |
| **Rate Limit** | 1/second | Higher |

💡 **Tip**: Add username/password to `.env` for unlimited searches!

---

## 🐛 Troubleshooting

### "API key not configured"
→ Set `OPENSUBTITLES_API_KEY` in `.env`

### "401 Unauthorized"
→ Invalid API key, get a new one

### "429 Too Many Requests"
→ Rate limit hit, add username/password or wait

### "No subtitles found"
→ Video not in database, try different release

See [Setup Guide](OPENSUBTITLES_SETUP.md) for detailed troubleshooting.

---

## 🔗 Useful Links

- [OpenSubtitles.com](https://www.opensubtitles.com)
- [API Documentation](https://opensubtitles.stoplight.io/docs/opensubtitles-api)
- [Get API Key](https://www.opensubtitles.com/en/consumers)
- [VIP Upgrade](https://www.opensubtitles.com/en/support) (~$10/year for 1000 downloads/day)

---

## 📦 What Changed?

### Removed:
- ❌ `subliminal==2.1.0` - Unreliable library
- ❌ `babelfish==0.6.0` - Outdated dependency

### Added:
- ✅ OpenSubtitles.com REST API integration
- ✅ Proper authentication system
- ✅ Clear error messages
- ✅ Better logging

### Result:
- 🎉 More reliable subtitle search
- 🚀 Faster downloads
- 🧹 Cleaner codebase
- 📝 Better documentation

---

## 🎊 Ready to Use!

1. Get your API key
2. Add it to `.env`
3. Start the app
4. Search for subtitles
5. Enjoy! 🍿

**Questions?** Check the [Setup Guide](OPENSUBTITLES_SETUP.md)
