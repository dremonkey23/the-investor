const { TwitterApi } = require('twitter-api-v2');
const c = new TwitterApi({
  appKey: 'YGNNPnFIyC5q55HWq7rjH9Bn1',
  appSecret: 'rKfDrfoUzutYJzgUonmouVQ0MFXy1cp7NFngfZykcqXT2l9uHd',
  accessToken: '1891489670313209856-xVzma3uhQPzIo5Aao00aMAjCWlJJtu',
  accessSecret: '5YRbxOkFckzAoaW9NBZT1TuRGmNAo61nHPod9G7BFmkv6',
});

const text = 'Day 3: AI managing $100K live. Currently at $100,937 (+0.94%). 13 positions, zero idle cash. Every trade public. Full website coming soon \u{1F4C8}';

c.v2.tweet(text).then(r => {
  console.log('Posted! ID:', r.data.id);
  console.log('Text:', r.data.text);
}).catch(e => {
  console.error('Error:', e.data || e.message);
});
