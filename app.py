import datetime
import flask
import redis

app = flask.Flask('shiyanlou-sse-chat')
app.secret_key = 'shiyanlou'
app.config['DEBUG'] = True
r = redis.StrictRedis()

# 主页路由函数
@app.route('/')
def home():
    # 如果用户未登录，重定向到登录页面
    if 'user' not in flask.session:
        return flask.redirect('/login')
    user = flask.session['user']
    return flask.render_template('home.html', user=user)

# 消息生成器
def event_stream():
    # 创建发布订阅系统
    pubsub = r.pubsub()
    # 使用发布订阅系统的 subscribe 方法订阅某个频道
    pubsub.subscribe('chat')
    for message in pubsub.listen():
        data = message['data']
        if type(data) == bytes:
            yield 'data: {}\n\n'.format(data.decode())

# 登录函数，首次访问需要登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        # 将用户名存到 session 字典里，然后重定向到首页
        flask.session['user'] = flask.request.form['user']
        return flask.redirect('/')
    return ('<form action="" method="post">User Name: <input name="user"> '
            '<input type="submit" value="login" /></form>')

# 接收 JavaScript 使用 POST 方法发送的数据
@app.route('/post', methods=['POST'])
def post():
    message = flask.request.form['message']
    user = flask.session.get('user', 'anonymous')
    now = datetime.datetime.now().replace(microsecond=0).time()
    r.publish('chat', '[{}] {}: {}\n'.format(now.isoformat(), user, message))
    return flask.Response(status=204)

# 事件流接口
@app.route('/stream')
def stream():
    # 该路由函数返回对象的数据类型须是 text/event-stream 类型
    return flask.Response(event_stream(), mimetype='text/event-stream')
