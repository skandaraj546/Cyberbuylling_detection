# CyberGuard - Real-time Cyberbullying Detection Platform

A modern, Twitter-like social media platform with real-time cyberbullying detection and prevention features. Built with Flask, WebSockets, and AI-powered content moderation.

## ✨ Features

- **Twitter-like Interface**: Modern glassmorphism design with real-time posting
- **Real-time Updates**: WebSocket-powered live feed updates
- **AI Content Moderation**: 
  - Gemini AI integration for text and image analysis
  - Local transformers fallback for offline detection
  - OCR text extraction from images
- **Smart Content Filtering**:
  - Automatic toxic content detection
  - Image blurring for offensive content
  - Keyword-based blocking
- **Interactive Features**:
  - Like, comment, and share posts
  - Report system for inappropriate content
  - User statistics and safety metrics
- **Twitter Integration**:
  - OAuth 2.0 authentication
  - Cross-platform posting (CyberGuard ↔ Twitter)
  - Real-time tweet streaming with toxicity detection
  - Automatic content moderation before tweeting
- **Responsive Design**: Works on desktop and mobile devices

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cyber-bulding/cyber-bulding
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (optional)
   Create a `.env` file in the project root (use `env_template.txt` as reference):
   ```env
   # AI Services (optional)
   GEMINI_API_KEY=your_gemini_api_key
   GROQ_API_KEY=your_groq_api_key
   
   # Twitter API Integration
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_api_secret
   TWITTER_BEARER_TOKEN=your_twitter_bearer_token
   TWITTER_CALLBACK_URL=http://localhost:5000/auth/twitter/callback
   
   # App Configuration
   SECRET_KEY=your_secret_key
   PORT=5000
   
   # Feature Flags
   USE_GEMINI=true
   USE_GROQ_BOT=true
   USE_TWITTER=true
   TOXICITY_THRESHOLD=0.5
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini AI API key | None |
| `GROQ_API_KEY` | Groq API key for bot responses | None |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `PORT` | Server port | `5000` |
| `USE_GEMINI` | Enable Gemini AI moderation | `true` |
| `USE_GROQ_BOT` | Enable AI bot responses | `true` |
| `TOXICITY_THRESHOLD` | Toxicity detection threshold (0-1) | `0.5` |

### AI Services Setup

#### Google Gemini AI
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set `GEMINI_API_KEY` environment variable
3. Gemini will handle text and image moderation

#### Groq AI Bot
1. Get API key from [Groq](https://console.groq.com/)
2. Set `GROQ_API_KEY` environment variable
3. Bot will provide helpful responses to users

#### Twitter Integration
1. Create a Twitter Developer App at [developer.twitter.com](https://developer.twitter.com/)
2. Get your API Key, API Secret, and Bearer Token
3. Set the environment variables:
   - `TWITTER_API_KEY`
   - `TWITTER_API_SECRET` 
   - `TWITTER_BEARER_TOKEN`
4. Users can connect their Twitter accounts and cross-post content

## 🎯 How It Works

### Content Moderation Flow

1. **Text Posts**: Analyzed using keyword filtering and AI models
2. **Image Uploads**: OCR text extraction + AI image analysis
3. **Real-time Detection**: Immediate blocking of toxic content
4. **User Feedback**: Report system for community moderation

### Safety Features

- **Automatic Blocking**: Toxic messages are blocked before posting
- **Image Blurring**: Offensive images are automatically blurred
- **Content Masking**: Blocked text is replaced with safe alternatives
- **User Reporting**: Community-driven content flagging

## 🎨 UI Components

### Glassmorphism Design
- Translucent backgrounds with backdrop blur
- Subtle borders and shadows
- Modern gradient color scheme

### Responsive Layout
- Three-column desktop layout
- Mobile-optimized single column
- Adaptive navigation and content areas

## 📱 Usage

### Posting Content
1. Enter your username
2. Type your message in the composer
3. Click "Post" or press Enter
4. Content is automatically moderated

### Image Uploads
1. Click the "Photo" button
2. Select an image file
3. Image is analyzed for safety
4. Offensive content is automatically blurred

### Interacting with Posts
- **Like**: Click the heart icon
- **Report**: Flag inappropriate content
- **Reveal**: Unblur blurred images (at your own risk)

## 🔒 Security Features

- **Content Filtering**: Multi-layer toxicity detection
- **User Privacy**: Anonymous posting available
- **Report System**: Community moderation tools
- **Safe Defaults**: Conservative content blocking

## 🛠️ Development

### Project Structure
```
cyber-bulding/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── static/            # CSS, JS, and uploads
│   ├── style.css      # Glassmorphism styles
│   ├── app.js         # Frontend logic
│   └── uploads/       # User image uploads
└── templates/         # HTML templates
    └── index.html     # Main interface
```

### Adding New Features
1. **Backend**: Extend Flask routes in `app.py`
2. **Frontend**: Update JavaScript in `static/app.js`
3. **Styling**: Modify CSS in `static/style.css`
4. **Templates**: Update HTML in `templates/`

## 🌟 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

- **Issues**: Report bugs via GitHub Issues
- **Features**: Request new features via GitHub Discussions
- **Security**: Report security issues privately

## 🔮 Future Enhancements

- [ ] User authentication and profiles
- [ ] Advanced AI moderation models
- [ ] Community guidelines and education
- [ ] Analytics dashboard
- [ ] Mobile app development
- [ ] Multi-language support

---

**CyberGuard** - Making the internet safer, one post at a time. 🛡️✨
