# -*- coding: utf-8 -*-

# requirements
import re, json
import requests
from bs4 import BeautifulSoup
import html5lib

# 处理cookie
cookies = json.load(open('zhihu_cookie.json'))
headers = {
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
}
# headers = {
#     'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
#     'Host': "www.zhihu.com",
#     'Origin': "http://www.zhihu.com",
#     'Pragma': "no-cache",
#     'Referer': "http://www.zhihu.com/",
#     'X-Requested-With': "XMLHttpRequest"
# }
rq = requests.Session()
rq.headers = headers
for cookie_item in cookies:
    rq.cookies[cookie_item['name']] = cookie_item['value']


def islogin():
    # check session
    url = "https://www.zhihu.com/settings/profile"
    r = rq.get(url, allow_redirects=False)
    status_code = int(r.status_code)
    if status_code == 301 or status_code == 302:
        # 未登录
        return False
    elif status_code == 200:
        return True
    else:
        raise Exception(u"网络故障")


class User:
    user_url = None
    r = None
    soup = None

    def __init__(self, user_url, user_id=None, data_id=None):
        if user_url == None:
            self.user_id = "匿名用户"
        elif user_url.startswith('www.zhihu.com/people', user_url.index('//') + 2) == False:
            raise ValueError("\"" + user_url + "\"" + " : it isn't a user url.")
        else:
            self.user_url = user_url
            print(self.user_url)
            print("this is user url")
            if user_id != None:
                self.user_id = user_id

            else:
                self.user_id = self.get_user_id()
                print(self.user_id)
                print("this is user id")
            if data_id != None:
                self.data_id = data_id
            else:
                self.data_id = self.get_data_id()
                print(self.data_id)
                print("this is user data id")

    def parser(self):
        self.r = rq.get(self.user_url)
        # print(self.r.content)
        # while self.r.status_code!=200:
        #     self.r = rq.get(self.user_url)
        #     print self.r.text
        # print(self.r.text.encode('utf-8'))
        # print(self.r.text)
        soup = BeautifulSoup(self.r.text, "html5lib")  # html.parser is better than lxml
        # print(soup.p)
        self.soup = soup

    def get_user_id(self):
        if self.user_url == None:
            # print "I'm anonymous user."
            return "匿名用户"
        else:
            ##            if self.soup == None:
            ##                print("cnmb")
            self.parser()
            # print(self.soup.p)
            soup = self.soup
            user_id0 = soup.find("div", class_="ProfileHeader-content")
            user_id = user_id0.find("span", class_="ProfileHeader-name").string
            # print(user_id)
            return user_id

    def get_data_id(self):
        # 增加获取知乎 data-id 的方法来确定标识用户的唯一性
        if self.user_url == None:
            print("I'm anonymous user.")
            return 0
        else:
            if self.r == None:
                self.parser()
            data_id = re.findall("urlToken&quot;:&quot;(.*?)&quot", self.r.text)[0]
            # print(data_id)
            return data_id

    def get_gender(self):
        # 增加获取知乎识用户的性别
        if self.user_url == None:
            print("I'm anonymous user.")
            return 'unknown'
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            try:
                gender = str(soup.find("span", class_="item gender").i)
                if (gender == '<i class="icon icon-profile-female"></i>'):
                    return 'female'
                else:
                    return 'male'
            except:
                return 'unknown'

    def get_followees_num(self):
        if self.user_url == None:
            print("I'm anonymous user.")
            return 0
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            followees_num = int(soup.find("div", class_="NumberBoard FollowshipCard-counts") \
                                .find("NumberBoard-value").strong.string)
            return followees_num

    def get_followers_num(self):
        if self.user_url == None:
            print("I'm anonymous user.")
            return 0
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            # followers_num = int(soup.find("div", class_="NumberBoard FollowshipCard-counts") \
            #                     .find_all("div", class_="NumberBoard-value")[1].strong.string)
            followers_num = int(soup.find("div", class_="NumberBoard FollowshipCard-counts") \
                                .find_all("div", class_="NumberBoard-value")[0].contents[0])
            print(followers_num)
            return followers_num

    def get_followees(self):
        if self.user_url == None:
            print("I'm anonymous user.")
            return
        else:
            followees_num = self.get_followees_num()
            if followees_num == 0:
                return
            else:
                followee_url = self.user_url + "/followees"
                r = rq.get(followee_url)
                # while r.status_code!=200:
                #     r = rq.get(followee_url)
                #     print r.text

                soup = BeautifulSoup(r.content, "html.parser")
                for i in xrange((followees_num - 1) / 20 + 1):
                    if i == 0:
                        user_url_list = soup.find_all("h2", class_="zm-list-content-title")
                        data_id_list = soup.find_all("div", class_="zg-right")
                        for j in xrange(min(followees_num, 20)):
                            data_id = data_id_list[j].find('button')['data-id'] if data_id_list[j].find(
                                'button') else None  # no button, actually when the followee is yourself
                            yield User(user_url_list[j].a["href"], user_url_list[j].a.string.encode("utf-8"), data_id)
                    else:
                        post_url = "http://www.zhihu.com/node/ProfileFolloweesListV2"
                        _xsrf = soup.find("input", attrs={'name': '_xsrf'})["value"]
                        offset = i * 20
                        hash_id = re.findall("hash_id&quot;: &quot;(.*)&quot;},", r.text)[0]
                        params = json.dumps({"offset": offset, "order_by": "created", "hash_id": hash_id})
                        data = {
                            '_xsrf': _xsrf,
                            'method': "next",
                            'params': params
                        }
                        header = {
                            'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0",
                            'Host': "www.zhihu.com",
                            'Referer': followee_url
                        }

                        r_post = rq.post(post_url, data=data, headers=header)

                        followee_list = r_post.json()["msg"]
                        for j in xrange(len(followee_list)):
                            followee_soup = BeautifulSoup(followee_list[j], "html.parser")
                            user_link = followee_soup.find("h2", class_="zm-list-content-title").a
                            data_id = followee_soup.find('button')['data-id'] if followee_soup.find(
                                'button') else None  # no button, actually when the followee is yourself
                            yield User(user_link["href"], user_link.string.encode("utf-8"), data_id)

    def get_followers(self):
        if self.user_url == None:
            print("I'm anonymous user.")
            return
        else:
            followers_num = self.get_followers_num()
            if followers_num == 0:
                return
            else:
                follower_url = self.user_url + "/followers"
                r = rq.get(follower_url)
                # while r.status_code!=200:
                #     r = rq.get(follower_url)
                #     print r.text

                soup = BeautifulSoup(r.content, "html.parser")
                for i in range(int((followers_num - 1) / 20 + 1)):
                    if i == 0:
                        user_url_list = soup.find_all("h2", class_="zm-list-content-title")
                        data_id_list = soup.find_all("div", class_="zg-right")
                        print(data_id_list)
                        for j in range(min(followers_num, 20)):
                            data_id = data_id_list[j].find('button')['data-id'] if data_id_list[j].find(
                                'button') else None  # no button, actually when the follower is yourself
                            yield User(user_url_list[j].a["href"], user_url_list[j].a.string.encode("utf-8"), data_id)
                    else:
                        post_url = "http://www.zhihu.com/node/ProfileFollowersListV2"
                        _xsrf = soup.find("input", attrs={'name': '_xsrf'})["value"]
                        offset = i * 20
                        hash_id = re.findall("hash_id&quot;: &quot;(.*)&quot;},", r.text)[0]
                        params = json.dumps({"offset": offset, "order_by": "created", "hash_id": hash_id})
                        data = {
                            '_xsrf': _xsrf,
                            'method': "next",
                            'params': params
                        }
                        header = {
                            'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0",
                            'Host': "www.zhihu.com",
                            'Referer': follower_url
                        }
                        r_post = rq.post(post_url, data=data, headers=header)

                        follower_list = r_post.json()["msg"]
                        for j in xrange(len(follower_list)):
                            follower_soup = BeautifulSoup(follower_list[j], "html.parser")
                            user_link = follower_soup.find("h2", class_="zm-list-content-title").a
                            data_id = follower_soup.find('button')['data-id'] if follower_soup.find(
                                'button') else None  # no button, actually when the follower is yourself
                            yield User(user_link["href"], user_link.string.encode("utf-8"), data_id)


if __name__ == '__main__':
    # print(islogin())
    # if islogin() != True:
    #     print "islogin() != True"
    #     raise Exception(u"无权限(403)")

    # r = rq.get('https://www.zhihu.com/people/hong-ming-da')
    # print r.content

    u = User('https://www.zhihu.com/people/wang-jian-31-98')
    # bad url test, switch from lxml to http.parser

    # print u.user_id
    # print u.data_id
    print(u.get_followers_num())
    # print u.get_followers()
    print(u.get_followees_num())
    for i in u.get_followees():
        print(i.data_id)
        print(i.user_id)
    # print u.get_followees()
    print(u.get_gender())
