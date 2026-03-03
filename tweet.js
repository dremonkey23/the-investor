// Twitter/X posting script for @TheinvestorAI
// Usage: node tweet.js (reads from tweet-draft.txt)
//    or: node tweet.js --text "your tweet here"
const fs = require('fs');
const path = require('path');
const { TwitterApi } = require('twitter-api-v2');

const client = new TwitterApi({
  appKey: 'YGNNPnFIyC5q55HWq7rjH9Bn1',
  appSecret: 'rKfDrfoUzutYJzgUonmouVQ0MFXy1cp7NFngfZykcqXT2l9uHd',
  accessToken: '1891489670313209856-xVzma3uhQPzIo5Aao00aMAjCWlJJtu',
  accessSecret: '5YRbxOkFckzAoaW9NBZT1TuRGmNAo61nHPod9G7BFmkv6',
});

async function tweet(text) {
  try {
    const result = await client.v2.tweet(text);
    console.log('✅ Tweet posted!');
    console.log(`ID: ${result.data.id}`);
    console.log(`Text: ${result.data.text}`);
    return result;
  } catch (e) {
    console.error('❌ Error:', e.code || '', e.data || e.message);
    if (e.data) console.error(JSON.stringify(e.data, null, 2));
  }
}

async function deleteTweet(id) {
  try {
    const result = await client.v2.deleteTweet(id);
    console.log('🗑️ Deleted tweet:', id);
    return result;
  } catch (e) {
    console.error('❌ Delete error:', e.data || e.message);
  }
}

// Parse args
const args = process.argv.slice(2);
if (args[0] === '--delete' && args[1]) {
  deleteTweet(args[1]);
} else {
  let text;
  if (args[0] === '--text') {
    text = args.slice(1).join(' ');
  } else if (args[0]) {
    text = args.join(' ');
  } else {
    // Read from tweet-draft.txt
    const draftPath = path.join(__dirname, 'tweet-draft.txt');
    if (fs.existsSync(draftPath)) {
      text = fs.readFileSync(draftPath, 'utf8').trim();
    } else {
      console.error('No text provided. Usage: node tweet.js --text "..." or create tweet-draft.txt');
      process.exit(1);
    }
  }
  tweet(text);
}
