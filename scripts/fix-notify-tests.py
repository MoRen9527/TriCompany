# -*- coding: utf-8 -*-
# notify 测试三案修（对齐 replay/confirm 语义）
import io

p = r'D:\Code\ai\TriMMC\test\notify-outbox.test.ts'
s = io.open(p, encoding='utf-8').read()

# 7 案：手写 200 条 doc（绕限速——跨分钟积累场景的直接构造）
old7 = """  it('上限：pending 满 → 503', () => {
    const path = freshPath();
    for (let i = 0; i < OUTBOX_MAX_PENDING; i++) {
      enqueueNotify({ source_seat: 'm-duty-cos', target_daemon: 'trimlc', target_seat: 'bod', urgent: 'normal', title: `t${i}`, body: 'b' }, path);
    }
    const r = ok(path, { message_id: undefined, title: 'over' });
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.statusCode, 503);
  });"""
new7 = """  it('上限：pending 满 → 503（直构 doc 绕限速——跨分钟积累场景）', () => {
    const path = freshPath();
    const dir = path.slice(0, path.lastIndexOf('\\\\')) || path.slice(0, path.lastIndexOf('/'));
    const messages = [];
    for (let i = 0; i < OUTBOX_MAX_PENDING; i++) {
      messages.push({
        message_id: `ntf-pre-${i}`, source_seat: 'm-duty-cos', target_daemon: 'trimlc', target_seat: 'bod',
        urgent: 'normal', title: `t${i}`, body: 'b', enqueued_at: new Date(Date.now() - 3600_000 + i * 1000).toISOString(),
        status: 'pending', status_history: [{ status: 'accepted', at: new Date().toISOString() }], attempts: 0,
      });
    }
    // 跨分钟错峰：全部落到窗口外，限速不触发
    for (const m of messages) m.enqueued_at = new Date(Date.now() - 3600_000).toISOString();
    writeFileSync(path, JSON.stringify({ messages }, null, 2) + '\\n', 'utf-8');
    void dir;
    const r = ok(path, { message_id: 'ntf-over', title: 'over' });
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.statusCode, 503);
  });"""
assert old7 in s, 'MISS 7'
s = s.replace(old7, new7)

# 8 案：补 confirm forwarded（三态历史才含 forwarded）
old8 = """  it('三态闭环：pending→delivered（精简两级）+状态史在卷+非法迁移拒', () => {
    const path = freshPath();
    ok(path);
    assert.equal(pullPending(path).length, 1);
    assert.equal(transitionStatus('ntf-test-1', 'delivered', path).ok, true);
    assert.equal(transitionStatus('ntf-test-1', 'forwarded', path).ok, false, 'delivered→forwarded 非法拒');
    const st = queryStatus('ntf-test-1', path);
    assert.equal(st[0].status, 'delivered');
    assert.ok(st[0].status_history.some((h) => h.status === 'forwarded'));
  });"""
new8 = """  it('三态闭环：pending→forwarded→delivered+状态史在卷+非法迁移拒', () => {
    const path = freshPath();
    ok(path);
    assert.equal(pullPending(path).length, 1, '拉取（replay）');
    assert.equal(transitionStatus('ntf-test-1', 'forwarded', path).ok, true, '收端 confirm forwarded');
    assert.equal(transitionStatus('ntf-test-1', 'delivered', path).ok, true, 'letter-store 终态 delivered');
    assert.equal(transitionStatus('ntf-test-1', 'forwarded', path).ok, false, 'delivered→forwarded 非法拒');
    const st = queryStatus('ntf-test-1', path);
    assert.equal(st[0].status, 'delivered');
    const history = st[0].status_history.map((h) => h.status);
    assert.deepEqual(history, ['accepted', 'forwarded', 'delivered']);
  });"""
assert old8 in s, 'MISS 8'
s = s.replace(old8, new8)

# 9 案：pull 后 confirm forwarded 才不重出（replay 语义）
old9 = """  it('拉取幂等：已拉走件不重出', () => {
    const path = freshPath();
    ok(path);
    assert.equal(pullPending(path).length, 1);
    assert.equal(pullPending(path).length, 0);
  });"""
new9 = """  it('replay 语义：未确认前重出/确认 forwarded 后不重出', () => {
    const path = freshPath();
    ok(path);
    assert.equal(pullPending(path).length, 1, '首拉');
    assert.equal(pullPending(path).length, 1, '未确认=重出（断链重投语义）');
    transitionStatus('ntf-test-1', 'forwarded', path);
    assert.equal(pullPending(path).length, 0, '确认 forwarded 后不重出');
  });"""
assert old9 in s, 'MISS 9'
s = s.replace(old9, new9)

io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('3 cases fixed')
