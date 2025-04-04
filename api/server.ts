import express from 'express';

const app = express();
const port = process.env.PORT || 1337;

app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Pipeline API is running' });
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
