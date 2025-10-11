# Twitter Integration Setup Guide

## Overview
CyberGuard now includes full Twitter integration, allowing users to connect their Twitter accounts and post directly to Twitter from the application.

## Features
- **Twitter OAuth Authentication** - Secure login with Twitter
- **Direct Posting** - Post messages to Twitter timeline
- **Real-time Status** - Live connection status indicator
- **Cross-posting** - Post to both CyberGuard and Twitter simultaneously
- **Disconnect Option** - Easy account disconnection

## Prerequisites
1. **Twitter Developer Account** - You need a Twitter Developer account
2. **Twitter App** - Create a Twitter app in the Developer Portal
3. **API Keys** - Obtain the required API credentials

## Step 1: Create Twitter Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Sign in with your Twitter account
3. Apply for a developer account if you don't have one
4. Complete the application process (may take a few days)

## Step 2: Create a Twitter App

1. In the Developer Portal, click "Create App"
2. Fill in the app details:
   - **App Name**: `CyberGuard` (or your preferred name)
   - **App Description**: `CyberGuard - Real-time Cyberbullying Detection Platform`
   - **Website URL**: `http://localhost:5000` (for development)
   - **Callback URL**: `http://localhost:5000/auth/twitter/callback`
   - **Terms of Service**: Your terms URL
   - **Privacy Policy**: Your privacy policy URL

3. **Enable OAuth 2.0**:
   - Go to "App Settings" → "Authentication Settings"
   - Enable "OAuth 2.0"
   - Set Callback URL: `http://localhost:5000/auth/twitter/callback`
   - Enable "Request email from users" (optional)

## Step 3: Get API Credentials

1. In your app dashboard, go to "Keys and Tokens"
2. Copy the following credentials:
   - **API Key** (Consumer Key)
   - **API Secret Key** (Consumer Secret)
   - **Bearer Token**

## Step 4: Configure Environment Variables

Create a `.env` file in your project root with the following variables:

```env
# Twitter API Integration
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_CALLBACK_URL=http://localhost:5000/auth/twitter/callback

# Enable Twitter integration
USE_TWITTER=true
```

## Step 5: Install Dependencies

The required dependencies are already included in `requirements.txt`:
- `tweepy==4.14.0` - Twitter API client
- `python-twitter-v2==2.1.0` - Additional Twitter utilities

Install them with:
```bash
pip install -r requirements.txt
```

## Step 6: Test the Integration

1. Start your CyberGuard application:
   ```bash
   python app.py
   ```

2. Navigate to `http://localhost:5000`
3. Login to your account
4. Look for the "Twitter Integration" section in the right sidebar
5. Click "Connect Twitter" to authenticate
6. Authorize the app on Twitter
7. You should see "Connected to Twitter" status

## Usage

### Connecting Twitter
1. In the main application, find the "Twitter Integration" section
2. Click "Connect Twitter"
3. You'll be redirected to Twitter for authorization
4. Authorize the app
5. You'll be redirected back with Twitter connected

### Posting to Twitter
1. Write your message in the post composer
2. Check "Also post to Twitter" checkbox (appears when connected)
3. Click "Post"
4. Your message will be posted to both CyberGuard and Twitter

### Disconnecting Twitter
1. In the Twitter Integration section
2. Click "Disconnect"
3. Confirm the disconnection
4. Twitter integration will be disabled

## API Endpoints

### Authentication
- `GET /auth/twitter` - Initiate Twitter OAuth
- `GET /auth/twitter/callback` - Handle OAuth callback

### Twitter API
- `GET /api/twitter/status` - Check connection status
- `POST /api/twitter/disconnect` - Disconnect from Twitter
- `POST /api/twitter/post` - Post directly to Twitter

### Enhanced Message API
- `POST /api/message` - Post message (now supports `postToTwitter` parameter)

## Security Considerations

### OAuth Flow
- Uses secure OAuth 2.0 flow
- No passwords stored
- Tokens are session-based
- Automatic token refresh

### Data Protection
- User tokens stored in server memory only
- No persistent storage of credentials
- Tokens cleared on logout
- Secure session management

## Troubleshooting

### Common Issues

#### 1. "Twitter integration not available"
- Check if `USE_TWITTER=true` in environment
- Verify all Twitter API keys are set
- Ensure tweepy is installed

#### 2. "Failed to get Twitter auth URL"
- Verify API Key and Secret are correct
- Check callback URL matches exactly
- Ensure OAuth 2.0 is enabled in Twitter app

#### 3. "Failed to post tweet"
- Check if user is connected to Twitter
- Verify Twitter app has write permissions
- Check for rate limiting

#### 4. OAuth Callback Issues
- Ensure callback URL is exactly: `http://localhost:5000/auth/twitter/callback`
- Check if port 5000 is accessible
- Verify no firewall blocking

### Debug Mode
Enable debug logging by setting:
```env
FLASK_DEBUG=1
```

### Rate Limiting
Twitter has rate limits:
- **Posting**: 300 tweets per 15-minute window
- **Authentication**: 15 requests per 15-minute window

## Production Deployment

### Environment Variables
For production, update your environment variables:
```env
TWITTER_CALLBACK_URL=https://yourdomain.com/auth/twitter/callback
```

### Twitter App Settings
1. Update your Twitter app settings:
   - **Website URL**: Your production domain
   - **Callback URL**: `https://yourdomain.com/auth/twitter/callback`
   - **Terms of Service**: Your production terms URL
   - **Privacy Policy**: Your production privacy policy URL

### Security
- Use HTTPS in production
- Set strong `SECRET_KEY`
- Consider using environment-specific Twitter apps
- Monitor API usage and rate limits

## Advanced Configuration

### Custom Scopes
To request additional permissions, modify the TwitterManager class in `app.py`:
```python
# Add scopes to OAuth request
self.auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
self.auth.set_access_token(access_token, access_token_secret)
```

### Error Handling
The integration includes comprehensive error handling:
- Network errors
- API rate limits
- Invalid credentials
- Permission errors

### Monitoring
Monitor Twitter integration with:
- Application logs
- Twitter API usage dashboard
- User feedback
- Error tracking

## Support

### Twitter API Documentation
- [Twitter API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
- [Tweepy Documentation](https://docs.tweepy.org/)

### CyberGuard Integration
- Check application logs for detailed error messages
- Verify environment variables are set correctly
- Test with a simple tweet first

## Next Steps

### Potential Enhancements
1. **Tweet Analytics** - Track engagement metrics
2. **Scheduled Posts** - Queue posts for later
3. **Hashtag Suggestions** - AI-powered hashtag recommendations
4. **Thread Support** - Create Twitter threads
5. **Media Upload** - Post images and videos to Twitter

### Integration with Other Platforms
The same pattern can be used to integrate with:
- Facebook
- LinkedIn
- Instagram
- Mastodon
- Bluesky

---

**Note**: This integration is designed for educational and development purposes. For production use, ensure compliance with Twitter's Terms of Service and implement proper error handling and monitoring.
