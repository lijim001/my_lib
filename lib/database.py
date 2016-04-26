#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
MySQLdb & Model
'''

import time
import json
import MySQLdb
import logging
from conf.settings import DB_CNF, options

class Mysql(object):
    '''
    封装MySQLdb
    '''
    min_cycle, max_cycle, total_time, counter, succ, fail, ext = 0xffffL, 0L, 0L, 0L, 0L, 0L, ''
    def __init__(self, dba, ismaster=False):
        '''
        @dba: 数据库账号信息
        @ismaster: 是否主库
        return: None
        '''
        self.dba = dba
        self.ismaster = ismaster
        self.conn = None
        self.cursor = None
        self.curdb = ''
        self.connect(dba)
        self.reset_stat()

    def __del__(self):
        '''
        关闭连接
        '''
        self.close()

    def __repr__(self):
        '''
        字符串表示
        '''
        return 'Mysql(%s)' % str(self.dba)

    def __str__(self):
        '''
        字符串表示
        '''
        return 'Mysql(%s)' % str(self.dba)

    def close(self):
        '''
        关闭数据库连接
        return: None
        '''
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None

    def connect(self, dba):
        '''
        连接到数据库
        @dba: 数据库账户信息
        return: None
        '''
        self.dba = dba
        self.conn = MySQLdb.connect(host=str(dba['host']), user=str(dba['user']),
                                    passwd=str(dba['passwd']), db=str(dba['db']),
                                    unix_socket=str(dba['sock']), port=dba['port'])
        self.cursor = self.conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        self.execute('set names utf8')
        self.execute('set autocommit=1')
        self.curdb = dba['db']

    def auto_reconnect(self):
        '''
        自动重连
        return: None
        '''
        try:
            self.conn.ping()
        except Exception, e:
            logging.warning('try to reconnect %s', str(e))
            try:
                self.cursor.close()
                self.conn.close()
            except MySQLdb.MySQLError, e:
                logging.warning('error when close old conn %s', str(e))
            self.connect(self.dba)

    def execute(self, sql, values=()):
        '''
        执行SQL语句
        @sql: 欲执行的SQL语句
        @values: SQL参数
        return: 执行结果
        '''
        # 确保在主库上执行'更新'操作
        if not self.ismaster and self.is_sql_update(sql):
            raise Exception('cannot execute[%s] on slave' % sql)
        start = time.time()
        self.auto_reconnect()
        if options.debug:
            logging.warn('%s, %s', sql, values)
        if sql.upper().startswith('SELECT'):
            result = self.cursor.execute(sql, values)
        else:
            result = self.cursor.execute(sql)
        self.update_stat((time.time() - start) * 1000, sql, values)
        return result

    def update_stat(self, spentime, sql, values):
        '''
        更新统计数据
        @spentime: 花费的时间
        @sql: 执行的SQL
        @values: SQL的参数
        return: None
        '''
        self.__class__.min_cycle = min(self.min_cycle, spentime)
        if spentime > self.__class__.max_cycle:
            self.__class__.max_cycle = spentime
            self.__class__.ext = '%s%%%s' % (sql, str(values))
        self.__class__.total_time += spentime
        self.__class__.counter += 1
        self.__class__.succ += 1

    @classmethod
    def reset_stat(cls):
        '''
        重置统计数据
        return: None
        '''
        cls.min_cycle, cls.max_cycle, cls.total_time = 0xffffL, 0L, 0L
        cls.counter, cls.succ, cls.fail, cls.ext = 0L, 0L, 0L, ''

    @classmethod
    def get_stat(cls):
        '''
        获得Mysql客户端执行的统计数据
        return: 统计数据
        '''
        return {
            'min_cycle':cls.min_cycle,
            'max_cycle':cls.max_cycle,
            'total_time':cls.total_time,
            'counter':cls.counter,
            'succ':cls.succ,
            'fail':cls.fail,
            'ext':cls.ext
        }

    @staticmethod
    def is_sql_update(sql):
        '''
        判断SQL语句是否是 '更新' 操作
        @sql: 待判断的SQL
        return: True OR False
        '''
        opers = ('INSERT', 'DELETE', 'UPDATE', 'CREATE', 'RENAME', 'DROP', 'ALTER',
                 'REPLACE', 'TRUNCATE')
        return sql.strip().upper().startswith(opers)

    def use_dbase(self, db_name):
        '''
        Use 相应的DB
        @db_name: 指定的DB
        return: None
        '''
        if self.curdb != db_name:
            self.execute('use %s' % db_name)
            self.curdb = db_name

    @staticmethod
    def merge_sql(where, cond):
        '''
        合并查询条件
        @where: 初始where语句
        @cond: 新增查询条件
        return: 合并后的查询条件
        '''
        return '%s AND %s' % (where, cond) if where and cond else (where or cond)

    def rows(self):
        '''
        取得所有查询结果
        '''
        return self.cursor.fetchall()

    @property
    def lastrowid(self):
        '''
        上次操作的记录ID
        '''
        return self.cursor.lastrowid

    def affected_rows(self):
        '''
        上次操作影响的记录数
        '''
        return self.conn.affected_rows()

    def connection(self):
        '''
        返回Mysql Connection
        '''
        return self.conn

class MysqlPool(object):
    '''
    Mysql Pool
    '''
    def __init__(self, dbcnf):
        '''
        初始化 '连接池', 每个db维护一个连接, 适应python单线程运行
        @dbcnf: 数据库配置, 如:
        DB_CNF = {
            'm':{
                    json.dumps(物理数据库实例_1):['逻辑数据库db组', ...],
                    json.dumps(物理数据库实例_2):['逻辑数据库db组', ...],
            },
            's':{
                    json.dumps(物理数据库实例_1):['逻辑数据库db组', ...],
                    json.dumps(物理数据库实例_2):['逻辑数据库db组', ...],
            }
        }
        '''
        # 存储逻辑DB Group到物理Mysql的映射
        self.cnf = {
            'm':{},
            's':{}
        }
        for role in ['m', 's']:
            for i in dbcnf[role]:
                for j in dbcnf[role][i]:
                    self.cnf[role][j] = json.loads(i)

        # 数据库连接池, m: master s: slave
        self.pool = {
            'm':{},
            's':{}
        }

    def get_server(self, db_name, db_group, ismaster=False):
        '''
        根据db_name、db group选择物理Mysql实例
        @db_name: 数据库名
        @db_group: 逻辑数据库组名, 我们根据组名来选择Mysql实例
        @ismaster: 是否主库
        return: Mysql连接
        '''
        cnf = (self.cnf['m'] if ismaster else self.cnf['s'])[db_group]
        cnf['db'] = db_name
        dbastr = '%s:%s:%s' % (cnf['host'], cnf['port'], cnf['db'])
        pool = self.pool['m'] if ismaster else self.pool['s']
        if dbastr not in pool:
            logging.debug('-->get_server: %s, %s, %s, %s', db_name, db_group,
                          dbastr, len(pool))
            pool[dbastr] = Mysql(cnf, ismaster=ismaster)
        return pool[dbastr]

    def disconnect_all(self):
        '''
        关闭所有的数据库连接
        return: None
        '''
        for role in ['m', 's']:
            for i in self.pool[role]:
                self.pool[role][i].close()

class Model(dict):
    '''
    Model
    '''
    _db = ''
    _table = ''
    _fields = set()
    _extfds = set()
    _pk = 'id'
    _scheme = ()
    _engine = 'InnoDB'
    _charset = 'utf8'
    def __init__(self, obj=None, dbinst=None, ismaster=False, **kargs):
        '''
        初始化ORM对象
        @obj: 对象的初始值
        @dbinst: 该对象所在的Mysql实例
        @ismaster: 是否主库
        @kargs: 分区字段, 选表、选库
        return: None
        '''
        obj = obj or {}
        super(Model, self).__init__(obj)
        self.ismaster = ismaster
        kargs.update(obj)
        self.dbinst = dbinst or self.get_dbserver(**kargs)
        self._changed = set()

    def get_dbserver(self, **kargs):
        '''
        根据ORM对象或分区字段获取Mysql实例
        @kargs: 分区字段, 选表、选库
        return: 到Mysql实例的连接
        '''
        db_name = self.get_dbase(**kargs)
        db_group = self.get_db_group(**kargs)
        return self.dpool.get_server(db_name, db_group, self.ismaster)

    @property
    def dpool(self):
        '''
        Mysql连接池
        '''
        if not hasattr(Model, '_dpool'):
            Model._dpool = MysqlPool(DB_CNF)
        return Model._dpool

    def __getattr__(self, name):
        '''
        定制ORM对象的属性访问
        @name: 属性名
        return: 属性值
        '''
        if (name in self._fields or name in self._extfds) and name in self:
            return self.__getitem__(name)
        return None

    def __setattr__(self, name, value):
        '''
        定制ORM对象的属性设置
        @name: 属性名
        @value: 属性值
        return: None
        '''
        flag = name in self._fields or name in self._extfds
        if name != '_changed' and flag and hasattr(self, '_changed'):
            if name in self._fields:
                self._changed.add(name)
            super(Model, self).__setitem__(name, value)
        else:
            self.__dict__[name] = value

    def __setitem__(self, name, value):
        '''
        定制ORM对象的ITEM设置
        @name: 属性名
        @value: 属性值
        return: None
        '''
        if name != '_changed' and name in self._fields and hasattr(self, '_changed'):
            self._changed.add(name)
        super(Model, self).__setitem__(name, value)

    def init_table(self, **kargs):
        '''
        初始化数据表
        @kargs: 分区字段信息
        return: None
        '''
        dbase = self.get_dbase(**kargs)
        if not self.is_dbase_exist(**kargs):
            self.dbinst.execute('CREATE DATABASE %s' % dbase)
        if not self.is_table_exist(**kargs):
            self.dbinst.use_dbase(dbase)
            scheme = ','.join(self._scheme)
            sql = 'CREATE TABLE `%s` (%s)ENGINE=%s DEFAULT CHARSET=%s'
            self.dbinst.execute(sql % (self.get_table(**kargs), scheme, self._engine, self._charset))

    def drop_table(self, **kargs):
        '''
        删除数据表
        @kargs: 分区字段信息
        return: None
        '''
        dbase = self.get_dbase(**kargs)
        if not self.is_dbase_exist(**kargs):
            raise Exception('%s not exist' % dbase)
        if self.is_table_exist(**kargs):
            self.dbinst.use_dbase(dbase)
            sql = 'DROP TABLE `%s`' % self.get_table(**kargs)
            self.dbinst.execute(sql)

    def before_replace(self):
        '''
        replace记录前被调用
        return: None
        '''
        pass

    def replace(self):
        '''
        执行Replace操作, 插入记录
        return: 当前插入的记录
        '''
        self.before_replace()
        self.dbinst.use_dbase(self.get_dbase(**self))
        sql = self._replace_sql()
        self.dbinst.execute(sql)
        if self._pk and self._pk not in self:
            self[self._pk] = self.dbinst.lastrowid
        return self

    def before_add(self):
        '''
        insert数据前被调用
        return: None
        '''
        pass

    def add(self):
        '''
        执行Insert操作, 插入记录
        return: 当前插入的记录
        '''
        self.before_add()
        self.dbinst.use_dbase(self.get_dbase(**self))
        sql = self._insert_sql()
        self.dbinst.execute(sql)
        if self._pk and self._pk not in self:
            self[self._pk] = self.dbinst.lastrowid
        return self

    def before_update(self):
        '''
        Update数据前被调用
        return: None
        '''
        pass

    def update(self, unikey=None):
        '''
        执行Update操作, 更新记录
        return: 当前更新的记录
        '''
        if self._changed:
            self.before_update()
            self.dbinst.use_dbase(self.get_dbase(**self))
            sql = self._update_sql(unikey)
            self.dbinst.execute(sql)
        return self

    def save(self):
        '''
        保存记录
        return: 当前保存的记录
        '''
        if self._pk in self:
            self.update()
        else:
            self.add()
        return self

    def before_delete(self):
        '''
        Delete记录前被调用
        return: None
        '''
        pass

    def delete(self, unikey=None):
        '''
        删除记录
        @unikey: 唯一键
        return: None
        '''
        self.before_delete()
        self.dbinst.use_dbase(self.get_dbase(**self))
        sql = self._delete_sql(unikey)
        self.dbinst.execute(sql)

    @classmethod
    def mgr(cls, ismaster=False, **kargs):
        '''
        ORM管理方法
        @cls: 当前类
        @ismaster: 是否主库
        @kargs: 用来选择不同Mysql实例的字段
        return: 当前ORM对象
        '''
        return cls(ismaster=ismaster, **kargs)

    @classmethod
    def new(cls, obj=None, dbinst=None, **kargs):
        '''
        创建新的ORM对象, 指向主库
        @obj: 初始属性
        @dbinst: Mysql实例的连接
        @kargs: 用来选择不同Mysql实例的字段
        return: 当前ORM对象
        '''
        return cls(obj, dbinst, ismaster=True, **kargs)

    def one(self, pk):
        '''
        根据主键获取记录
        '''
        return self.Q().filter(id=pk)[0]

    def Q(self, **kargs):
        '''
        构造查询
        @kargs: 数据分区字段, 用来分表
        return: 查询对象
        '''
        return Query(self, **kargs)

    def raw(self, sql, values=(), **kargs):
        '''
        执行原始SQL
        @sql: SQL语句
        @values: SQL的参数
        @kargs: 用来选择不同Mysql实例的字段
        return: 记录列表
        '''
        self.dbinst.use_dbase(self.get_dbase(**kargs))
        self.dbinst.execute(sql, values)
        return self.dbinst.rows()

    @property
    def lastrowid(self):
        '''
        取得上次插入记录的ID
        '''
        return self.dbinst.lastrowid

    def get_db_group(self, **kargs):
        '''
        取得 '逻辑' 数据库分组, 根据DB分组来选择在哪个Mysql实例上
        @kargs: 用来取得数据库分组
        return: 分组名
        '''
        return self._db

    def get_dbase(self, **kargs):
        '''
        取得数据库DB名
        @kargs: 用来取得数据库名
        return: DB名
        '''
        return self._db

    def get_table(self, **kargs):
        '''
        取得数据表名
        @kargs: 用来取得数据表名
        return: 表名
        '''
        return self._table

    def is_dbase_exist(self, **kargs):
        '''
        数据库是否存在
        @kargs: 用来取得数据库名
        return: True OR False
        '''
        dbase = self.get_dbase(**kargs)
        sql = "select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = '%s'"
        self.dbinst.execute(sql % dbase)
        rows = self.dbinst.rows()
        return True if rows else False

    def is_table_exist(self, **kargs):
        '''
        判断表是否已经存在
        @kargs: 用来取得数据表名
        return: True OR False
        '''
        dbname = self.get_dbase(**kargs)
        tablename = self.get_table(**kargs)
        values = (tablename, dbname)
        sql = "select TABLE_NAME from information_schema.TABLES where TABLE_NAME='%s' AND TABLE_SCHEMA='%s'"
        self.dbinst.execute(sql % values)
        rows = self.dbinst.rows()
        return True if rows else False

    def _insert_sql(self):
        '''
        组装插入SQL
        return: 最终的Insert SQL
        '''
        obj = self
        table = self.get_table(**obj)
        domains = ','.join(['`%s`' % e for e in obj if e in self._fields])
        values  = ','.join(["'%s'" % MySQLdb.escape_string(str(obj[e]))
                            for e in obj if e in self._fields])
        return 'INSERT INTO %s (%s) VALUES (%s)' % (table, domains, values)

    def _replace_sql(self):
        '''
        组装插入SQL
        return: 最终的Replace SQL
        '''
        obj = self
        table = self.get_table(**obj)
        domains = ','.join(['`%s`' % e for e in obj if e in self._fields ])
        values  = ','.join(["'%s'" % MySQLdb.escape_string(str(obj[e]))
                            for e in obj if e in self._fields])
        return 'REPLACE INTO %s (%s) VALUES (%s)' % (table, domains, values)

    def _update_sql(self, unikey=None):
        '''
        组装更新SQL
        return: 最终的Update SQL
        '''
        obj = self
        table = self.get_table(**obj)
        uni = unikey or self._pk
        values_up  = ','.join(["`%s`='%s'" % (e, MySQLdb.escape_string(str(obj[e])))
                               for e in obj if e!=uni and e in self._changed])
        return "UPDATE %s SET %s WHERE `%s`='%s'" % (table, values_up, uni, str(obj[uni]))

    def _delete_sql(self, unikey=None):
        '''
        组装删除SQL
        return: 最终的Delete SQL
        '''
        obj = self
        table = self.get_table(**obj)
        uni = unikey or self._pk
        return "DELETE FROM %s WHERE `%s`='%s'" % (table, uni, obj[uni])

class Query(object):
    '''
    查询对象
    '''
    def __init__(self, model=None, qtype='SELECT *', **kargs):
        '''
        初始化查询对象
        @model: ORM对象
        @qtype: 查询类型
        @kargs: 用来选择Mysql实例、Mysql表
        return: None
        '''
        self.model = model
        self.cache = None
        self.qtype = qtype
        self.conditions = {}
        self.limit = ()
        self.extras = []
        self.order = []
        self.group = []
        self.placeholder = '%s'
        self.kargs = kargs

    def __getitem__(self, k):
        '''
        定制下表操作
        @k: 下标值
        return: ORM对象 或 ORM对象列表
        '''
        if self.cache:
            return self.cache[k]
        if isinstance(k, (int, long)):
            self.limit = (k, 1)
            _list = self.data()
            return _list[0] if _list else None
        elif isinstance(k, slice):
            if k.start is not None:
                assert k.stop and k.stop >= k.start
                self.limit = k.start, (k.stop - k.start)
            elif k.stop is not None:
                self.limit = 0, k.stop
        return self.data()

    def __len__(self):
        '''
        定制长度方法
        '''
        return len(self.data())

    def __iter__(self):
        '''
        定制迭代
        '''
        return iter(self.data())

    def __repr__(self):
        '''
        定制字符标示
        '''
        return repr(self.data())

    def filter(self, **kwargs):
        '''
        查询某个字段
        @kargs: 待查询的字段
        return: 查询对象自身
        '''
        self.cache = None
        self.conditions.update(kwargs)
        return self

    def extra(self, *args):
        '''
        额外的查询条件
        @args: 待查询的条件
        return: 查询对象自身
        '''
        self.cache = None
        self.extras.extend([i for i in args if i])
        return self

    def orderby(self, field, direction='ASC'):
        '''
        按指定字段排序
        @field: 指定的字段
        @direction: 升序 or 降序
        return: 查询对象自身
        '''
        self.cache = None
        self.order.append((field, direction))
        return self

    def _get_orderbys(self):
        '''
        取得排序子句
        '''
        order_list  = ['`%s` %s' % (i, j) for i, j in self.order]
        return 'ORDER BY %s' % ','.join(order_list) if order_list else ''

    def groupby(self, field):
        '''
        按指定字段分组
        @field: 指定字段
        return: 查询对象自身
        '''
        self.cache = None
        self.group.append(field)
        return self

    def _get_groupbys(self):
        '''
        取得groupby子句
        '''
        group_list  = ['`%s`' % i for i in self.group]
        return 'GROUP BY %s' % ','.join(group_list) if group_list else ''

    def set_limit(self, start, size):
        '''
        设置limit
        @start: Limit offset
        @size: 记录条数
        return: 查询对象自身
        '''
        self.limit = start, size
        return self

    def _get_limit(self):
        '''
        取得Limit子句
        '''
        return 'LIMIT %s' % ', '.join(str(i) for i in self.limit) if self.limit else ''

    def _get_condition_keys(self):
        '''
        取得Where条件子句
        '''
        where = ''
        if self.conditions:
            where = ' AND '.join('`%s`=%s' % (k, self.placeholder) for k in self.conditions)
        if self.extras:
            where = Mysql.merge_sql(where, ' AND '.join([i.replace('%', '%%') for i in self.extras]))
        return 'WHERE %s' % where if where else ''

    def _get_condition_values(self):
        '''
        取得条件子句的参数值
        '''
        return list(self.conditions.itervalues())

    def query_template(self):
        '''
        取得查询模板
        '''
        return '%s FROM %s %s %s %s %s' % (
                self.qtype,
                self.model.get_table(**self.kargs),
                self._get_condition_keys(),
                self._get_groupbys(),
                self._get_orderbys(),
                self._get_limit()
                )

    def count(self):
        '''
        查询记录数
        '''
        if self.cache is None:
            _qtype = self.qtype
            self.qtype = 'SELECT COUNT(1) AS CNT'
            rows = self.query()
            self.qtype = _qtype
            return rows[0]['CNT'] if rows else 0
        else:
            return len(self.cache)

    def data(self):
        '''
        取得记录列表, 元素为ORM对象
        return: ORM对象列表
        '''
        if self.cache is None:
            self.cache = list(self.iterator())
        return self.cache

    def iterator(self):
        '''
        迭代器
        '''
        for row in self.query():
            obj = self.model.__class__(row, dbinst=self.model.dbinst,
                                       ismaster=self.model.ismaster)
            yield obj

    def query(self):
        '''
        执行查询
        return: row列表, 元素为单条原始记录, 为dict
        '''
        values = self._get_condition_values()
        return self.model.raw(self.query_template(), values, **self.kargs)

