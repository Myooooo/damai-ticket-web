import os
from time import sleep
import pickle  # 保存和读取cookie实现免登陆的一个工具
from selenium import webdriver  # 操作浏览器的工具
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

"""
一. 实现免登陆
二. 抢票并且下单
"""

# 下载Chrome Web Driver: https://chromedriver.chromium.org/downloads
# 将chromedriver.exe与此文件放在同一目录

# 大麦网主页
damai_url = 'https://m.damai.cn/damai/home/index.html'
# 登录
login_url = 'https://m.damai.cn/damai/minilogin/index.html?returnUrl=https%3A%2F%2Fm.damai.cn%2Fdamai%2Fmine%2Fmy%2Findex.html%3Fspm%3Da2o71.home.top.duserinfo&spm=a2o71.0.0.0'
# 抢票目标页
target_url = 'https://m.damai.cn/damai/detail/item.html?itemId=611160757855&spm=a2o71.search.list.ditem_2'
# chromedriver目录
driver_path = os.path.join(os.path.dirname(__file__),'./chromedriver.exe')
# cookie目录
cookie_path = os.path.join(os.path.dirname(__file__),'./cookies.pkl')
# 购票数量，需提前填好实名信息
n_tickets = 2

# class Concert:
class Concert:
    # 初始化加载
    def __init__(self):
        self.status = 0  # 状态, 表示当前操作执行到了哪个步骤
        self.login_method = 1  # {0:模拟登录, 1:cookie登录}自行选择登录的方式
        self.service = Service(executable_path=driver_path)
        self.driver = webdriver.Chrome(service=self.service)  # 当前浏览器驱动对象

    # cookies: 登录网站时出现的 记录用户信息用的
    def set_cookies(self):
        """cookies: 登录网站时出现的 记录用户信息用的"""
        self.driver.get(damai_url)
        print('###请点击登录###')
        # 我没有点击登录,就会一直延时在首页, 不会进行跳转
        while self.driver.title.find('大麦') != -1:
            sleep(1)
        print('###请扫码登录###')
        # 没有登录成功
        while self.driver.title != '大麦':
            sleep(1)
        print('###扫码成功###')
        # get_cookies: driver里面的方法
        pickle.dump(self.driver.get_cookies(), open(cookie_path, 'wb'))
        print('###cookie保存成功###')
        self.driver.get(target_url)

    # 假如说我现在本地有 cookies.pkl 那么 直接获取
    def get_cookie(self):
        """假如说我现在本地有 cookies.pkl 那么 直接获取"""
        cookies = pickle.load(open(cookie_path, 'rb'))
        for cookie in cookies:
            cookie_dict = {
                'domain': '.damai.cn',  # 必须要有的, 否则就是假登录
                'name': cookie.get('name'),
                'value': cookie.get('value')
            }
            self.driver.add_cookie(cookie_dict)
        print('###载入cookie###')

    def login(self):
        """登录"""
        if self.login_method == 0:
            self.driver.get(login_url)
            print('###开始登录###')
        elif self.login_method == 1:
            # 创建文件夹, 文件是否存在
            if not os.path.exists(cookie_path):
                self.set_cookies()  # 没有文件的情况下, 登录一下
            else:
                self.driver.get(target_url)  # 跳转到抢票页
                self.get_cookie()  # 并且登录

    def enter_concert(self):
        """打开浏览器"""
        print('###打开浏览器,进入大麦网###')
        # 调用登录
        self.login()  # 先登录再说
        self.driver.refresh()  # 刷新页面
        self.status = 2  # 登录成功标识
        print('###登录成功###')
        # 处理弹窗
        if self.isElementExist('/html/body/div[2]/div[2]/div/div/div[3]/div[2]'):
            self.driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div/div[3]/div[2]').click()

    # 二. 抢票并且下单
    def choose_ticket(self):
        """选票操作"""
        if self.status == 2:
            print('=' * 30)
            print('###开始进行日期及票价选择###')
            while self.driver.title.find("订单确认页") == -1:
                try:
                    buybutton = self.driver.find_element(By.CLASS_NAME, 'buy__button').text
                    if buybutton == '缺货登记':
                        print("###缺货重试###")
                        sleep(0.5)
                        self.status = 2  # 没有进行更改操作
                        self.driver.get(target_url)  # 刷新页面 继续执行操作
                        continue
                    if buybutton == '开售提醒':
                        print("###未开售###")
                        sleep(0.5)
                        self.status = 2  # 没有进行更改操作
                        self.driver.get(target_url)  # 刷新页面 继续执行操作
                        continue
                    elif buybutton == '立即预定':
                        # 点击立即预定
                        self.driver.find_element('buy__button').click()
                        self.status = 3
                    elif buybutton == '立即购买':
                        self.driver.find_element(By.CLASS_NAME, 'buy__button').click()
                        self.status = 4
                    elif buybutton == '选座购买':
                        self.driver.find_element(By.CLASS_NAME, 'buy__button').click()
                        self.status = 5
                except:
                    print('###没有跳转到订单结算界面###')
                
                # 检查选座弹窗是否存在
                if self.driver.find_elements(By.CLASS_NAME, 'sku-content'):
                    # 有弹窗，尝试选座购买
                    success = self.choice_seats()
                    # 无可用座次，刷新网页
                    if not success:
                        self.driver.refresh()
                        continue

                title = self.driver.title
                if title == '订单确认页':
                    # 实现下单的逻辑
                    while True:
                        # 如果标题为确认订单
                        print('正在加载.......')

                        if self.driver.find_elements(By.CLASS_NAME, 'viewer'):
                            self.check_order()
                            break

    def choice_seats(self):
        """选择座位，适用于类似周杰伦的场次->座位逻辑，默认选择最早/便宜的可用座位"""

        # 获取场次
        sessions = self.driver.find_elements(By.CLASS_NAME, 'bui-dm-sku-card-item')
        n_sessions = len(sessions)
        
        # 筛选可用场次
        flag = False
        for s in sessions:
            if not s.find_elements(By.CLASS_NAME,'item-tag-outer'):
                # 场次可用
                s.click()
                flag = True
                break

        # 如果有可用场次，筛选可用座位
        if flag:
            # 排除场次的元素
            cats = self.driver.find_elements(By.CLASS_NAME, 'bui-dm-sku-card-item')
            cats = cats[n_sessions,:]

            for c in cats:
                if not c.find_elements(By.CLASS_NAME,'item-tag-outer'):
                    # 座位可用，点击确认
                    c.click()
                    # 按需增加票数
                    if n_tickets > 1:
                        for i in range(n_tickets - 1):
                            if self.driver.find_elements(By.CLASS_NAME, 'plus-enable'):
                                self.driver.find_element(By.CLASS_NAME, 'plus-enable').click()
                    self.driver.find_element(By.CLASS_NAME, 'sku-footer-buy-button').click()
                    return True
        return False

    def check_order(self):
        """下单操作"""  
        if self.status in [3, 4, 5]:
            print('###开始确认订单###')
            sleep(1)
            try:
                # 选择前n个实名观众，已登记观众数最好和购票数量一致
                div_viewer = self.driver.find_element(By.CSS_SELECTOR, '.viewer div')
                viewers = div_viewer.find_elements(By.CSS_SELECTOR, 'div')
                for i in range(min(len(viewers), n_tickets)):
                    viewers[i].click()

                # 已选中，提交订单
                if self.driver.find_elements(By.CLASS_NAME, 'icondanxuan-xuanzhong_'):
                    # 最后一步提交订单
                    sleep(0.5)  # 太快了不好, 影响加载 导致按钮点击无效
                    btn = self.driver.find_element(By.CSS_SELECTOR, "div[view-name='FrameLayout'] > div[style='position: absolute; display: flex; font-size: 29px; width: 100%; -webkit-box-pack: center; justify-content: center; -webkit-box-align: center; align-items: center; color: rgb(255, 255, 255); height: 100%; overflow: hidden; max-width: none;']")
                    btn.click()
                    sleep(20)
                else: 
                    raise Exception('###购票人信息选中失败, 自行查看元素位置###')
            except Exception as e:
                print(e)

    def isElementExist(self, element):
        """判断元素是否存在"""
        flag = True
        browser = self.driver
        try:
            browser.find_element(By.XPATH, element)
            return flag
        except:
            flag = False
            return flag

    def finish(self):
        """抢票完成, 退出"""
        self.driver.quit()


if __name__ == '__main__':
    con = Concert()
    try:
        con.enter_concert()  # 打开浏览器
        con.choose_ticket()  # 选择座位
    except Exception as e:
        print(e)
        con.finish()
