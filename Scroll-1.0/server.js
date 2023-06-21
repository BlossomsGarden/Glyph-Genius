const express = require('express');
const app = express();
const path = require('path');

// 指定静态文件夹
app.use(express.static(__dirname));

// 重定向 / 到 t.html
app.get('/', function(req, res) {
  res.redirect('/t.html');
});

// 启动服务器并监听端口
const port = 8092;
app.listen(port, function() {
  console.log(`Server is listening on port ${port}...`);
});