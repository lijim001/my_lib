#coding=utf-8

import simplejson as json
#import json
from django.http import HttpResponse
from MobileService.util.InstanceMessage import InstanceMessageUtil
from MobileService.util.session_manage import *

from django.conf import settings

ERROR_NO_ERROR = 0
#common error from 0xx
ERROR_USER_NEED_LOGIN = 1
ERROR_USER_NO_USER_NAME = 2
ERROR_USER_NO_PASSWD = 3
ERROR_USER_LOGIN_FAILED = 4
ERROR_USER_NOT_FOUND_USER_NAME = 5
ERROR_USER_INVALID_PASSWD = 6
ERROR_USER_INVALID_PHONE_NUM = 7
ERROR_USER_PHONE_NUM_ALREADY_EXISTS = 8
ERROR_USER_INVALID_PIN_CODE = 9
ERROR_USER_REGISTER_FAILED = 10
ERROR_USER_POSITION_INVALID = 11
ERROR_INVILID_HTTP_REQUEST_METHOD = 12
ERROR_INVILID_OLD_PASSWORD = 13
ERROR_USER_FORGET_PASSWD_FAILED = 14
ERROR_USER_NEED_SALES_NAME = 15
ERROR_USER_NO_PRIVILEGE = 16
ERROR_USER_MAX_MESSAGE_TIMES = 17
ERROR_USER_UPDATE_SHOP_INFO_FAILED = 18
ERROR_USER_BANK_INFO_NO_BANK_NUMBER = 19
ERROR_USER_BANK_INFO_NO_IDENTITY = 20
ERROR_USER_BANK_INFO_NO_BANK_ID = 21
ERROR_USER_INVALID_BANK_ID = 22
ERROR_USER_INVALID_NO_IDENTITY = 23
ERROR_USER_INVALID_BANK_NUMBER = 24
ERROR_USER_UPDATE_BANK_INFO_FAILED = 25
ERROR_USER_NO_INVITATION_CODE = 26
ERROR_USER_INVITATION_CODE_NOT_FOUND = 27
ERROR_USER_INVITATION_CODE_MAX_USAGE_TIMES = 28
ERROR_USER_CHANGE_ROLE_FAILED = 29
ERROR_USER_CHANGE_ORDER_COMMISION_FAILED = 30
ERROR_USER_INVALID_INVITATION_CODE = 31
ERROR_USER_INVALID_INVITATION_CODE_TYPE = 32
ERROR_USER_INVITATION_CODE_HAS_BINDED = 33
ERROR_USER_INVITATION_CODE_CAN_NOT_BIND_SELF = 34
ERROR_USER_NO_COMISSION_NEED_SETTLE = 35
ERROR_USER_SETTLE_COMISSION_FAILED = 36
ERROR_USER_SAVE_SETTLE_COMISSION_FAILED = 37
ERROR_USER_INVALID_NO_BANK_PHONE = 38
ERROR_USER_NOT_ENOUGH_COUPON = 39
ERROR_USER_PULL_COUPON_FAILED = 40
ERROR_USER_NO_TEST_USER = 41
ERROR_COUPON_PAY_FAILED = 42
ERROR_SET_USER_INFO_FAILED = 43
ERROR_BIND_UPPER_SALES_FAILED = 44
ERROR_USER_CAN_NOT_BIND_SELF_PHONE = 45
ERROR_USER_FORBID_THIS_OPERATION = 46
ERROR_CREATE_USER_FORBID_FAILED = 47
ERROR_USER_HAS_BINDED_UPPER_SALES = 48
ERROR_USER_UPLOAD_BUSINESS_CARD_FAILED = 49
ERROR_USER_NEED_UPDATE_PACKET = 50
ERROR_USER_UPDATE_NON_BANK_INFO_FAILED = 51
ERROR_USER_NO_CATEGORY_INFO = 52
ERROR_USER_CAN_NOT_FOUND_SALES = 53
ERROR_USER_NOT_VERIFIED_SALES = 54
ERROR_USER_SETTLE_COMISSION_FORBID = 55
ERROR_USER_UPLOAD_SCORE_IMAGE_EMPTY = 56
ERROR_USER_SETTLE_COMISSION_NOT_REACH_MONEY = 57
ERROR_USER_SETTLE_COMISSION_USER_NOT_VERIFIED = 58
ERROR_USER_CHANGE_PASSWD_FAILED = 59
ERROR_USER_INVITE_CUSTOMER_FUNCTION_FORBID = 60
ERROR_USER_LACK_PARAMETER = 61
ERROR_USER_CALLBACK_FAILED = 62
ERROR_NOTE_SEND_FAILED = 63
ERROR_USER_NOT_PAY_PRIVILEGE = 64
ERROR_USER_UPLOAD_ORDER_IMAGE_TOO_MANY = 65
ERROR_USER_APPLYING_PAY_PRIVILEGE = 66
ERROR_COMMENT_CAN_NOT_EMPTY = 67
ERROR_COMMENT_CREATE_ERROR = 68
ERROR_COMMENT_SALES_CREATE_ERROR = 69
ERROR_COMMENT_NOT_EXIST = 70
ERROR_COMMENT_CAN_NOT_REPLY = 71
ERROR_USER_PHONE_RECHARGE_NOT_SUPPORT = 72
ERROR_USER_INVITE_SALES_NOT_SUPPORT = 73

#order error from 1xx
ERROR_ORDER_NO_PRICE = 100
ERROR_ORDER_INVALID_TYPE = 101
ERROR_ORDER_CREATE_FAILED = 102
ERROR_ORDER_NOT_FOUND = 103
ERROR_ORDER_CHECK_FAILED = 104
ERROR_ORDER_MODIFY_INFO_FAILED = 105
ERROR_ORDER_CANCEL_FAILED = 106
ERROR_ORDER_INVALID_OREDER_NUMBER = 107
ERROR_ORDER_CREATE_PREPAY_ORDER_FAILED = 108
ERROR_ORDER_UPLOAD_CONTRACT_IMAGE_FAILED = 109
ERROR_ORDER_CONTRACT_REACH_MAX = 110
ERROR_ORDER_CAN_NOT_CHANGE_SHOP = 111
ERROR_ORDER_CUSTOMER_NOT_FOUND = 112
ERROR_ORDER_CURRENT_PRICE_BIG_THAN_TOTAL = 113
ERROR_ORDER_SALES_NOT_VERIFIED = 114
ERROR_ORDER_NOT_ORDER_OWNER = 115
ERROR_ORDER_PAYED = 116
ERROR_ORDER_PAY_MONEY_BIG_THAN_CONTRACT = 117
ERROR_ORDER_EMPTY_SALES_PHONE = 118
ERROR_ORDER_INVALID_REAL_PAY_MONEY = 119
ERROR_ORDER_ORDER_NUMBER_EMPTY = 120
ERROR_ORDER_CUSTOMER_CAN_NOT_CREATE = 121
ERROR_ORDER_CONTRACT_PRICE_ZERO = 122
ERROR_ORDER_OFFLINE_PAY_FAILED = 123
ERROR_ORDER_SEND_SO_BIG_MONEY = 124
ERROR_ORDER_COOPERATION_XINWO_CUSTOMER_NO_PERMIT_RANDOM_CUTOFF = 125
ERROR_ORDER_GET_PERCENT_COUPON_FAILED = 126
ERROR_ORDER_CAN_NOT_USE_THIS_PERCENT_COUPON = 127
ERROR_ORDER_CAN_NOT_PAYED = 128
ERROR_ORDER_CUSTOMER_CAN_NOT_USE_THIS_PAY = 129

#wallet error from 2xx
ERROR_WALLET_SET_PASSWD_FAILED = 200
ERROR_WALLET_PAY_PASSWORD_EMPTY = 201
ERROR_WALLET_CHANGE_PASSWD_FAILED = 202
ERROR_WALLET_INVALID_PAY_PASSWORD = 203
ERROR_WALLET_NOT_ENOUGH_MONEY = 204
ERROR_WALLET_USING_COUPON = 205
ERROR_WALLET_PAY_FAILED = 206
ERROR_WALLET_INVALID_PAY_TYPE = 207
ERROR_WALLET_ROLLOUT_FAILED = 208
ERROR_WALLET_FORGET_PASSWD_FAILED = 209

#pay error from 3xx
ERROR_PAY_UPOP_CREATE_URL_FAILED = 300
ERROR_PAY_ONLINE_FOR_PRE_COOPERATION_SALES = 301

#shop error from 4xx
ERROR_SHOP_NOT_FOUND_SHOP = 400
ERROR_SHOP_NOT_MATCH_INVATION_CODE = 401
ERROR_SHOP_EMPTY_SHOP_NAME_OR_BRAND_NAME = 402
ERROR_SHOP_NOT_FOUND_SHOP_POSITION = 403

#system error from 5xx
ERROR_OPERATION_FAILED = 500
ERROR_INVALID_PRIVILEGE = 501
ERROR_INVALID_ROLE = 502

#activity error from 6xx
ERROR_REWARD_HAS_BEEN_DRAWED = 600
ERROR_REWARD_SET_REWARD_NAME_FAILED = 601
ERROR_REWARD_NOT_FOUND_REWARD = 602
ERROR_REWARD_REWARD_NAME_EMPTY = 603

#inquiry error from 7xx
ERROR_INQUIRY_SEND_MESSAGE_FAILED = 700
ERROR_INQUIRY_CONTENT_CAN_NOT_EMPTY = 701
ERROR_INQUIRY_GOODS_NOT_FOUND = 702
ERROR_INQUIRY_CREATE_INQUIRY_FAILED = 703
ERROR_INQUIRY_CREATE_INQUIRY_TOO_FREQUENT = 704
ERROR_INQUIRY_NEED_TALK_TARGET = 705
ERROR_INQUIRY_NOT_FOUND_GOODS = 706
ERROR_INQUIRY_SEND_SHOP_ADDR_FAILED = 707
ERROR_INQUIRY_BUSINESS_FORBID = 708
ERROR_INQUIRY_GOODS_MODIFY_FAILED = 709
ERROR_INQUIRY_GOODS_CONTENT_CAN_NOT_EMPTY = 710
ERROR_INQUIRY_GOODS_MONEY_CAN_NOT_EMPTY = 711
ERROR_INQUIRY_GOODS_IMAGE_CAN_NOT_EMPTY = 712
ERROR_INQUIRY_GOODS_REMOVE_FAILED = 713
ERROR_INQUIRY_GOODS_SEND_TWICE = 714
ERROR_INQUIRY_COPY_ITEM_FAILED = 715

#promote error from 8xx
ERROR_PROMOTE_SALES_HAS_BEEN_INVITED = 800
ERROR_PROMOTE_INVALID_DATE = 801
ERROR_PROMOTE_PRE_COOPERATION_NOT_ENOUGH_INFO = 802
ERROR_PROMOTE_PRE_COOPERATION_APPLY_FAILED = 803
ERROR_PROMOTE_PRE_COOPERATION_NO_PRIVILEGE = 804
ERROR_PROMOTE_PRE_COOPERATION_CAN_NOT_APPLY_AGAIN = 805
ERROR_PROMOTE_PRE_COOPERATION_STOP = 806
ERROR_PROMOTE_PRE_COOPERATION_SALES_APPLY_NO_USER = 807
ERROR_PROMOTE_PRE_COOPERATION_SALES_APPLY_NO_VERIFY = 808
ERROR_PROMOTE_PRE_COOPERATION_SALES_FIRST_APPLY_FAILED = 809
ERROR_PROMOTE_PRE_COOPERATION_SALES_LAST_APPLY_FAILED = 810
ERROR_PROMOTE_OPEN_PAY_PRIVILEGE_FAILED = 811
ERROR_PROMOTE_ACCOUNT_DISABLED = 812
ERROR_PROMOTE_FILL_SALES_PHONE_FAILED = 813

#coupon error from 9xx
ERROR_COUPON_ADD_SHOPPING_LIST_FAILED = 900
ERROR_COUPON_APPLY_GIFT_MONEY_FAILED = 901

#goods error from 10xx
ERROR_GOODS_IMAGE_MODIFY_COUNT_NOT_MATCH = 1000
ERROR_GOODS_NOT_FOUND_GOODS = 1001
ERROR_GOODS_MODIFY_FAILED = 1002
ERROR_GOODS_CUTOFF_MONEY_BIG_THAN_MONEY = 1003

#book shop from 11xx
ERROR_BOOK_SHOP_SAME_SHOP_SAME_DAY = 1100

msg_dict={
        #common error from 0xx
        ERROR_USER_NEED_LOGIN: '用户需要进行登录',
        ERROR_USER_NO_USER_NAME: '用户名不能为空',
        ERROR_USER_NO_PASSWD: '密码不能为空',
        ERROR_USER_LOGIN_FAILED: '用户登录失败',
        ERROR_USER_NOT_FOUND_USER_NAME: '用户名不存在',
        ERROR_USER_INVALID_PASSWD: '登陆密码错误',
        ERROR_USER_INVALID_PHONE_NUM: '手机号非法',
        ERROR_USER_PHONE_NUM_ALREADY_EXISTS: '用户名已经存在',
        ERROR_USER_INVALID_PIN_CODE: '验证码错误',
        ERROR_USER_REGISTER_FAILED: '注册失败',
        ERROR_USER_POSITION_INVALID: '经纬度坐标格式错误',
        ERROR_INVILID_HTTP_REQUEST_METHOD: '请求方法不正确',
        ERROR_INVILID_OLD_PASSWORD: '不正确的老密码',
        ERROR_USER_FORGET_PASSWD_FAILED: '忘记密码失败',
        ERROR_USER_NEED_SALES_NAME: '缺少销售人员名字',
        ERROR_USER_NO_PRIVILEGE: '无权限',
        ERROR_USER_MAX_MESSAGE_TIMES: '达到短信发送次数上限',
        ERROR_USER_UPDATE_SHOP_INFO_FAILED: '更新店铺信息失败',
        ERROR_USER_BANK_INFO_NO_BANK_NUMBER: '缺少银行账户信息',
        ERROR_USER_BANK_INFO_NO_IDENTITY: '缺少身份证信息',
        ERROR_USER_BANK_INFO_NO_BANK_ID: '未完善银行卡信息，请进入「我的」>「设置」>「奖励提取方式」中完善银行卡信息。',
        ERROR_USER_INVALID_BANK_ID:'错误的银行ID',
        ERROR_USER_INVALID_NO_IDENTITY: '身份证格式错误',
        ERROR_USER_INVALID_BANK_NUMBER: '银行卡号格式错误',
        ERROR_USER_UPDATE_BANK_INFO_FAILED: '更新用户银行信息失败',
        ERROR_USER_NO_INVITATION_CODE: '缺少邀请码',
        ERROR_USER_INVITATION_CODE_NOT_FOUND: '未找到邀请码',
        ERROR_USER_INVITATION_CODE_MAX_USAGE_TIMES: '邀请码达到最大使用上限',
        ERROR_USER_CHANGE_ROLE_FAILED: '修改用户角色失败',
        ERROR_USER_CHANGE_ORDER_COMMISION_FAILED: '修改订单结算信息失败',
        ERROR_USER_INVALID_INVITATION_CODE: '非法的邀请码',
        ERROR_USER_INVALID_INVITATION_CODE_TYPE: '错误的邀请码类型',
        ERROR_USER_INVITATION_CODE_HAS_BINDED: '该用户已经绑定过邀请码',
        ERROR_USER_INVITATION_CODE_CAN_NOT_BIND_SELF: '不能邀请自己',
        ERROR_USER_NO_COMISSION_NEED_SETTLE: '没有可以提现的金额',
        ERROR_USER_SETTLE_COMISSION_FAILED: '未完善银行卡信息，请进入「我的」>「设置」>「奖励提取方式」中完善银行卡信息。',
        ERROR_USER_SAVE_SETTLE_COMISSION_FAILED: '修改佣金结算失败',
        ERROR_USER_INVALID_NO_BANK_PHONE: '缺少银行绑定手机号',
        ERROR_USER_NOT_ENOUGH_COUPON: '优惠卷金额不足',
        ERROR_USER_PULL_COUPON_FAILED: '提取优惠卷失败',
        ERROR_USER_NO_TEST_USER: '该用户不是系统测试账号',
        ERROR_COUPON_PAY_FAILED: '优惠卷支付失败',
        ERROR_SET_USER_INFO_FAILED: '设置个人信息失败',
        ERROR_BIND_UPPER_SALES_FAILED: '绑定邀请店员失败',
        ERROR_USER_CAN_NOT_BIND_SELF_PHONE: '不能绑定自己的手机号',
        ERROR_USER_FORBID_THIS_OPERATION: '您被禁止进行该项操作',
        ERROR_CREATE_USER_FORBID_FAILED: '创建禁止数据失败',
        ERROR_USER_HAS_BINDED_UPPER_SALES: '已经绑定过店员',
        ERROR_USER_UPLOAD_BUSINESS_CARD_FAILED: '上传名片失败',
        ERROR_USER_NEED_UPDATE_PACKET: '使用此功能请升级到新版本',
        ERROR_USER_UPDATE_NON_BANK_INFO_FAILED:'更新支付宝账号失败',
        ERROR_USER_NO_CATEGORY_INFO: '缺少分类信息',
        ERROR_USER_CAN_NOT_FOUND_SALES : '无法找到店员信息',
        ERROR_USER_NOT_VERIFIED_SALES: '您的个人资料未通过新窝认证，请关注新版本并升级',
        ERROR_USER_SETTLE_COMISSION_FORBID: '系统已不再支持手动提现，请关注新版本并升级',
        ERROR_USER_UPLOAD_SCORE_IMAGE_EMPTY: '晒片图片不能为空',
        ERROR_USER_SETTLE_COMISSION_NOT_REACH_MONEY: '攒够100元再领取吧^_^',
        ERROR_USER_SETTLE_COMISSION_USER_NOT_VERIFIED: '认证通过后才可领取奖励',
        ERROR_USER_CHANGE_PASSWD_FAILED: '修改密码失败',
        ERROR_USER_INVITE_CUSTOMER_FUNCTION_FORBID: '邀请顾客奖励活动已结束',
        ERROR_USER_LACK_PARAMETER: '缺少参数',
        ERROR_USER_CALLBACK_FAILED: '回呼处理失败',
        ERROR_NOTE_SEND_FAILED: '短信发送失败',
        ERROR_USER_NOT_PAY_PRIVILEGE: '您没有开通支付权限，请联系客服开通',
        ERROR_USER_UPLOAD_ORDER_IMAGE_TOO_MANY: '上传图片不能超过3张',
        ERROR_USER_APPLYING_PAY_PRIVILEGE: '您的开通申请已提交，请等待新窝工作人员联系您。如有问题，请联系新窝官方客服400-890-0988。',
        ERROR_USER_PHONE_RECHARGE_NOT_SUPPORT: '手机充值领取方式已取消，给您造成的不便敬请谅解。',        
        ERROR_USER_INVITE_SALES_NOT_SUPPORT : '店员邀请活动已下线，给您造成不便敬请谅解。',
        
        ERROR_COMMENT_CAN_NOT_EMPTY: '咨询内容不能为空',
        ERROR_COMMENT_CREATE_ERROR: '咨询创建失败',
        ERROR_COMMENT_SALES_CREATE_ERROR: '回复咨询失败',
        ERROR_COMMENT_NOT_EXIST: '回复的咨询不存在',
        ERROR_COMMENT_CAN_NOT_REPLY: '该咨询不能再次回复',

        
        #order error from 1xx
        ERROR_ORDER_NO_PRICE:'价钱不能为空',
        ERROR_ORDER_INVALID_TYPE: '全款、订金类型错误',
        ERROR_ORDER_CREATE_FAILED: '订单创建失败',
        ERROR_ORDER_NOT_FOUND: '查找订单失败',
        ERROR_ORDER_CHECK_FAILED: '检查订单失败',
        ERROR_ORDER_MODIFY_INFO_FAILED: '修改订单失败',
        ERROR_ORDER_CANCEL_FAILED: '取消订单失败',
        ERROR_ORDER_INVALID_OREDER_NUMBER: '订单号不合法',
        ERROR_ORDER_CREATE_PREPAY_ORDER_FAILED: '生成支付预订单失败',
        ERROR_ORDER_UPLOAD_CONTRACT_IMAGE_FAILED: '上传合同图片失败',
        ERROR_ORDER_CONTRACT_REACH_MAX: '已经达到最大上传合同图片数量',
        ERROR_ORDER_CAN_NOT_CHANGE_SHOP: '不能修改订单的门店',
        ERROR_ORDER_CUSTOMER_NOT_FOUND: '未找到相应顾客',
        ERROR_ORDER_CURRENT_PRICE_BIG_THAN_TOTAL: '本次支付金额不能大于合同金额',
        ERROR_ORDER_SALES_NOT_VERIFIED: '您没有通过认证，不能生成订单',
        ERROR_ORDER_NOT_ORDER_OWNER: '您支付的不是自己创建的订单',
        ERROR_ORDER_PAYED: '该订单已经完成支付',
        ERROR_ORDER_PAY_MONEY_BIG_THAN_CONTRACT: '支付金额大于合同金额',
        ERROR_ORDER_EMPTY_SALES_PHONE: '您输入的店员手机号不能为空',
        ERROR_ORDER_INVALID_REAL_PAY_MONEY: '实付金额有误',
        ERROR_ORDER_ORDER_NUMBER_EMPTY : '缺少订单号',
        ERROR_ORDER_CUSTOMER_CAN_NOT_CREATE: '系统已经不支持顾客主动发起支付',
        ERROR_ORDER_CONTRACT_PRICE_ZERO: '合同价钱不能为0',
        ERROR_ORDER_OFFLINE_PAY_FAILED: '订单线下支付失败',
        ERROR_ORDER_SEND_SO_BIG_MONEY: '发送失败，顾客可享受补贴的门店金额上限为60000元，请修改后重新发送。',
        ERROR_ORDER_COOPERATION_XINWO_CUSTOMER_NO_PERMIT_RANDOM_CUTOFF:'合作店员禁止为新窝顾客发送随机立减订单',
        ERROR_ORDER_GET_PERCENT_COUPON_FAILED:'获取优惠劵失败',
        ERROR_ORDER_CAN_NOT_USE_THIS_PERCENT_COUPON:'不可使用该补贴券',
        ERROR_ORDER_CAN_NOT_PAYED: '该订单不可支付',
        ERROR_ORDER_CUSTOMER_CAN_NOT_USE_THIS_PAY: '该顾客不能使用该种支付方式',
        
        #order error from 2xx
        ERROR_WALLET_SET_PASSWD_FAILED: '设置家居宝支付密码失败',
        ERROR_WALLET_PAY_PASSWORD_EMPTY: '家居宝支付密码为空',
        ERROR_WALLET_CHANGE_PASSWD_FAILED: '修改家居宝支付密码失败',
        ERROR_WALLET_INVALID_PAY_PASSWORD: '支付密码错误',
        ERROR_WALLET_NOT_ENOUGH_MONEY: '账号余额不足',
        ERROR_WALLET_PAY_FAILED: '支付失败',
        ERROR_WALLET_INVALID_PAY_TYPE: '错误支付类型',
        ERROR_WALLET_ROLLOUT_FAILED: '提现操作失败',
        ERROR_WALLET_FORGET_PASSWD_FAILED: '忘记密码操作失败',
        
        #pay error from 3xx
        ERROR_PAY_UPOP_CREATE_URL_FAILED: '生成银联支付链接失败',
        ERROR_PAY_ONLINE_FOR_PRE_COOPERATION_SALES : '试用店员发送的订单，已不支持线上付款',
        
        #shop error from 4xx
        ERROR_SHOP_NOT_FOUND_SHOP: '未找到商店信息',
        ERROR_SHOP_NOT_MATCH_INVATION_CODE: '商铺与邀请码不符',
        ERROR_SHOP_EMPTY_SHOP_NAME_OR_BRAND_NAME: '店铺名或者品牌名为空',
        ERROR_SHOP_NOT_FOUND_SHOP_POSITION: '无找到店铺位置信息',
        #system error from 5xx
        ERROR_OPERATION_FAILED: '操作失败',
        ERROR_INVALID_PRIVILEGE: '不正确的权限值',
        ERROR_INVALID_ROLE: '不正确的角色值',
        
        #activity error from 6xx
        ERROR_REWARD_HAS_BEEN_DRAWED: '奖励已经领取',
        ERROR_REWARD_SET_REWARD_NAME_FAILED: '选择奖励操作失败',
        ERROR_REWARD_NOT_FOUND_REWARD: '未发现相关奖品信息',
        ERROR_REWARD_REWARD_NAME_EMPTY: '奖品不能为空',
        
        ERROR_INQUIRY_SEND_MESSAGE_FAILED: '发送消息失败',
        ERROR_INQUIRY_CONTENT_CAN_NOT_EMPTY: '消息内容不能为空',
        ERROR_INQUIRY_GOODS_NOT_FOUND: '询价商品不存在',
        ERROR_INQUIRY_CREATE_INQUIRY_FAILED: '创建询价失败',
        ERROR_INQUIRY_CREATE_INQUIRY_TOO_FREQUENT: '不能在短时间创建多个询价',
        ERROR_INQUIRY_NEED_TALK_TARGET: '缺少聊天对象',
        ERROR_INQUIRY_NOT_FOUND_GOODS: '未找到相关商品',
        ERROR_INQUIRY_SEND_SHOP_ADDR_FAILED: '发送店铺地址失败',
        ERROR_INQUIRY_BUSINESS_FORBID: '您已经被该顾客禁止回复',
        ERROR_INQUIRY_GOODS_MODIFY_FAILED: '修改店铺商品失败',
        ERROR_INQUIRY_GOODS_CONTENT_CAN_NOT_EMPTY: '商品描述不能为空',
        ERROR_INQUIRY_GOODS_MONEY_CAN_NOT_EMPTY: '商品价格不能为空',
        ERROR_INQUIRY_GOODS_IMAGE_CAN_NOT_EMPTY: '商品不能没有图片',
        ERROR_INQUIRY_GOODS_REMOVE_FAILED: '删除店铺商品失败',
        ERROR_INQUIRY_GOODS_SEND_TWICE: '不允许重复发送同样的商品',
        ERROR_INQUIRY_COPY_ITEM_FAILED:'复制比价失败',
        
        
        ERROR_PROMOTE_SALES_HAS_BEEN_INVITED: '店员已经被邀请过',
        ERROR_PROMOTE_INVALID_DATE: '日期格式不正确',
        ERROR_PROMOTE_PRE_COOPERATION_NOT_ENOUGH_INFO: '申请资料不全',
        ERROR_PROMOTE_PRE_COOPERATION_APPLY_FAILED: '试合作申请失败',
        ERROR_PROMOTE_PRE_COOPERATION_NO_PRIVILEGE: '没有权限修改该申请资料',
        ERROR_PROMOTE_PRE_COOPERATION_CAN_NOT_APPLY_AGAIN: '试用中不可再次申请',
        ERROR_PROMOTE_PRE_COOPERATION_STOP: '试用已经终止',
        ERROR_PROMOTE_PRE_COOPERATION_SALES_APPLY_NO_USER: '该用户不存在',
        ERROR_PROMOTE_PRE_COOPERATION_SALES_APPLY_NO_VERIFY: '通过认证之后，再申请合作吧',
        ERROR_PROMOTE_PRE_COOPERATION_SALES_FIRST_APPLY_FAILED: '申请试合作失败',
        ERROR_PROMOTE_PRE_COOPERATION_SALES_LAST_APPLY_FAILED: '申请正式合作失败',
        ERROR_PROMOTE_OPEN_PAY_PRIVILEGE_FAILED : '开通支付失败',
        ERROR_PROMOTE_ACCOUNT_DISABLED : '该地推账号已经不可用',
        ERROR_PROMOTE_FILL_SALES_PHONE_FAILED: '您输入的手机号码错误',
        
        ERROR_COUPON_ADD_SHOPPING_LIST_FAILED: '添加购物车失败',
        ERROR_COUPON_APPLY_GIFT_MONEY_FAILED: '申请现金劵失败',
        
        #goods error from 10xx
        ERROR_GOODS_IMAGE_MODIFY_COUNT_NOT_MATCH: '修改商品图片数量不一致',
        ERROR_GOODS_NOT_FOUND_GOODS: '未找到要修改的商品',
        ERROR_GOODS_MODIFY_FAILED: '商品修改失败',
        ERROR_GOODS_CUTOFF_MONEY_BIG_THAN_MONEY: '折扣价不能大于原价',
        
        #book shop from 11xx
        ERROR_BOOK_SHOP_SAME_SHOP_SAME_DAY: '你已经预约过该门店，请您选择其他日期或者门店',
        }

MOBILE_INFO_COMMENT_ORDER = '''
    pay_type: 付款类型, 0 未知,1 表示家居宝,2 表示立减付,3 表示混合付款
    seq: 该订单的序号,用于分页获取数据的start值
    channel_id:供货商ID,一个供货商下可能存在多个门店
    channel_name:供货商名称
    shop_id:门店ID
    shop_name:门店名称
    price_total:该账单的总钱数,类型为浮点数
    price_pre:订金钱数,类型为浮点数
    create_type:订单创建类型, 1表示看货订单,2就是移动端创建的订单
    sales:销售人员标识
    state:0 未付款 1 定金已付款 2 已付款 3 已取消 4 已退货, 可用于生成操作按钮
    price_real:实际付款额
    pre_flag:是否带有订金,0 不含订金 1 含有订金
    '''
    
COMMENT_LIST ={
        1 : MOBILE_INFO_COMMENT_ORDER
        }
        
from decimal import *
getcontext().prec = 3

def response_error_json(error_code, param_dict={}, extra_info=''):
    response = json.dumps({'result': 'failure', 'data': param_dict, 'error_code' : error_code, 'error_msg': msg_dict[error_code], 'extra':extra_info})
    return HttpResponse(response, content_type='application/json')

def handle_message_count(request):
    if request:
        user_phone = session_get_user_name(request)
        is_c = None
        if session_is_customer_user(request):
            is_c = True
        elif session_is_business_user(request):
            is_c = False
            
        if is_c is not None:
            handler = InstanceMessageUtil(settings.COMMON_DATA)
            count = handler.get_message_count(user_phone, is_c)
            if not count:
                count = 0
            return count
    return 0
        
def response_success_json(param_dict={}, request=None):
    if not param_dict:
        param_dict = {}
       
    output_param_dict = {}
    output_param_dict['data'] = param_dict
    output_param_dict['result'] = 'success'
    output_param_dict['error_code'] = 0
    output_param_dict['error_msg'] = ''
    output_param_dict['im_count'] = 0
    if request:
        output_param_dict['im_count'] = handle_message_count(request)
    response = json.dumps(output_param_dict, use_decimal=True)
    #print response
    return HttpResponse(response, content_type='application/json')
    
