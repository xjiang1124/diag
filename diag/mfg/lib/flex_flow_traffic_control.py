import redis
import sys
import time
import random
import threading
from functools import partial
from datetime import datetime
from libmfg_cfg import FLEX_FLOW_TOKEN_REDIS_IP
from libmfg_cfg import FLEX_FLOW_TOKEN_REDIS_PASSWD

class FlexFlowTrafficControl(object):
    """
    Flex Flow network traffic control class
    """

    def __init__(self, mtp_mgmt_ctrl=None):
        self.mtp_mgmt_ctrl = mtp_mgmt_ctrl
        redis_ip = FLEX_FLOW_TOKEN_REDIS_IP.strip()  if  FLEX_FLOW_TOKEN_REDIS_IP.strip() else "localhost"
        self.redis_con = redis.StrictRedis(
                                            host=redis_ip,
                                            port=6379,
                                            db=0,
                                            password=FLEX_FLOW_TOKEN_REDIS_PASSWD,
                                            decode_responses=True)
        self.max_red_light_on_time = 3600
        self.max_tokens = None
        self.token_life_span = None
        self.red_light_on_timestamp = None
        # to avoid multiple MTP in the same step of request redis server access
        self.sleep_interval =random.randint(10, 20)

    def _log_display(self, msg, critical_level="info", display_level=0):

        if critical_level == 'info':
            if self.mtp_mgmt_ctrl:
                self.mtp_mgmt_ctrl.cli_log_inf(msg, display_level)
            else:
                print(msg)
        elif critical_level == "warn":
            if self.mtp_mgmt_ctrl:
                self.mtp_mgmt_ctrl.cli_log_wrn(msg, display_level)
            else:
                print(msg)
        elif critical_level == "error":
            if self.mtp_mgmt_ctrl:
                self.mtp_mgmt_ctrl.cli_log_err(msg, display_level)
            else:
                print(msg)
        else:
            pass

    def _warning_fail_log(self, msg, critical_level="warn"):

        # save the warning log into redis list with key FLEX_FLOW_TOKEN_LOGS, we keep 1000 log entries
        # critical_level should be one of 'warn' of 'fail'
        now = datetime.now()
        msg = now.strftime("[%Y-%m-%d_%H-%M-%S]") + ' ' + critical_level.upper() + ": " + msg

        redisCom = partial(self.redis_con.llen)
        rc = self._redisCommand(redisCom, 'FLEX_FLOW_TOKEN_LOGS')
        if rc == -1:
            self._log_display("Get FLEX_FLOW_TOKEN_LOGS length Failed", "warn")
            # return False
        if int(rc) > 1000:
            redisCom = partial(self.redis_con.lpop)
            rc = self._redisCommand(redisCom, 'FLEX_FLOW_TOKEN_LOGS')
            if rc == -1:
                self._log_display("Failed POP FLEX_FLOW_TOKEN_LOGS", "warn")
                # return False
        
        redisCom = partial(self.redis_con.rpush)
        rc = self._redisCommand(redisCom, 'FLEX_FLOW_TOKEN_LOGS', msg)
        if rc == -1:
            self._log_display("Failed Push given message to FLEX_FLOW_TOKEN_LOGS", "warn")
            return False
        return True

    def _redisCommand(self, command=None, *args, **keywords):
        """
        excute redis command, return result
        """

        if  command is None:
            return -1

        try:
            rc = command(*args, **keywords)
        except Exception as Err:
            self._log_display('Error:'+str(Err), "error")
            return -1
        return rc

    def _get_flex_flow_avialable_token(self):
        """
        return a possiable token string candidate and latest number of used tokens
        """

        all_tokens_index = set([i+1 for i in range(self.max_tokens)])
        my_sleep_interval = self.sleep_interval
        starving = ""
        redisCom =  partial(self.redis_con.keys)
        rc = self._redisCommand(redisCom, 'FLEX_FLOW_REDIS_TOKEN_*')
        if rc == -1:
            return -1, None
        if self.red_light_on_timestamp is None:
            self.red_light_on_timestamp = time.time()
        used_tokens = rc

        while (self.max_tokens - len(used_tokens)) == 0:
            now = time.time()
            if now - self.red_light_on_timestamp > self.max_red_light_on_time:
                self._log_display("Traffic Light on Red over {:d} seconds, exit the Traffic Control System".format(self.max_red_light_on_time))
                self._warning_fail_log("Traffic Light on Red over {:d} seconds, exit the Traffic Control System".format(self.max_red_light_on_time), "fail")
                return -1, None
            # if one MTP is starving(for example,  wait more than 10 mins), decrease the waiting time, so that this MTP got more chance. 
            if now - self.red_light_on_timestamp > 600:
                my_sleep_interval = my_sleep_interval-1 if my_sleep_interval > 1 else 1
                starving = "starving"
            self._log_display('No Available Tokens,{:s} retry in {:d} seconds...'.format(starving, my_sleep_interval))
            time.sleep(my_sleep_interval)
            rc = self._redisCommand(redisCom, 'FLEX_FLOW_REDIS_TOKEN_*')
            if rc == -1:
                return -1, None
            used_tokens = rc

        used_tokens_index = [ int(i.replace('FLEX_FLOW_REDIS_TOKEN_', '')) for i in used_tokens]
        used_tokens_index = set(used_tokens_index)
        available_token_index = all_tokens_index - used_tokens_index
        new_token_index = available_token_index.pop()
        new_token = 'FLEX_FLOW_REDIS_TOKEN_' + str(new_token_index)

        return new_token, len(used_tokens)

    def _set_flex_flow_token(self):
        """
        return a available token 
        """

        set_token_fail = True
        self._log_display("Traffic Light is On Red")

        while set_token_fail:
            if self.red_light_on_timestamp:
                if time.time() - self.red_light_on_timestamp > self.max_red_light_on_time:
                    self._log_display("Traffic Light on Red over {:d} seconds, exit the Traffic Control System without waiting".format(self.max_red_light_on_time))
                    return False
            new_token, used_tokens_number = self._get_flex_flow_avialable_token()
            if new_token == -1:
                return False
            # set token tag as used
            redisCom =  partial(self.redis_con.set)
            rc = self._redisCommand(redisCom, new_token, "1", ex=self.token_life_span, nx=True)
            if rc == -1:
                return False
            if rc:
                set_token_fail = False
                break

        self._log_display('Got Token: {:s}'.format(new_token))

        # statistic
        redisCom =  partial(self.redis_con.keys)
        rc1 = self._redisCommand(redisCom, 'FLEX_FLOW_REDIS_TOKEN_*')
        used_tokens_count = used_tokens_number + 1 if rc1 == -1 else len(rc1)
        redisCom = partial(self.redis_con.set)
        now = datetime.now()
        statistic_key = 'FLEX_FLOW_TOKEN_COUNT#{:d}{:d}{:d}#{:d}:{:d}:{:d}.{:d}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond)
        # keep two weeks of the used token number statistic history
        used_token_static_history = 3600 * 24 * 14
        rc = self._redisCommand(redisCom, statistic_key, used_tokens_count, ex=used_token_static_history)
        if  rc == -1:
            self._log_display("Set statistic key {:s} value {:d} failed".format(statistic_key, used_tokens_count), "warn")
            # save the warning log into redis list with key FLEX_FLOW_TOKEN_LOGS, we keep 1000 log entries
            self._warning_fail_log("Set statistic key {:s} value {:d} failed".format(statistic_key, used_tokens_count), "warn")

        return new_token

    def is_workable(self):
        """
        ping redis connection
        return True if ping pass, otherwise return False
        """
        try:
            ping_res = self.redis_con.ping()
        except Exception as Err:
            self._log_display('Error:'+str(Err))
            self._log_display('Failed to connect, terminating.')
            return False
        else:
            if ping_res:
                self._log_display('Redis Server Connected!')
                return True
            else:
                return False

    def is_green_light_on(self):
        """
        if get a valid token, set the green light to on and return the token, otherwise False
        """

        # get flex flow max allowed tokens
        redisCom =  partial(self.redis_con.get)
        rc = self._redisCommand(redisCom, 'FLEX_FLOW_MAX_ALLOWED_TOKENS')
        if rc == -1:
            self._log_display("Get FLEX_FLOW_MAX_ALLOWED_TOKENS From Redis, Failed value {:s}".format(str(rc)), "error")
            return False
        self.max_tokens = int(rc)

        # get flex flow token life span
        redisCom =  partial(self.redis_con.get)
        rc = self._redisCommand(redisCom, 'FLEX_FLOW_TOKENS_LIFE_SPAN')
        if rc == -1:
            self._log_display("Get FLEX_FLOW_TOKENS_LIFE_SPAN From Redis, Failed value {:s}".format(str(rc)), "error")
            return False
        self.token_life_span = rc

        token = self._set_flex_flow_token()
        return token
    
    def release_token(self, token=None):
        """
        release the given token
        """
        if token is None:
            return False

        redisCom =  partial(self.redis_con.delete)
        rc = self._redisCommand(redisCom, token)
        if rc == -1:
            return False
        self._log_display("Flow Flow Traffic Control Release Token: {:s}".format(token))
        return rc

def unitest():
    my_traffic = FlexFlowTrafficControl()

    if my_traffic.is_workable():
        print("Flow Flow Traffic Control System is ready")
        green_light_token = my_traffic.is_green_light_on()
        if green_light_token:
            print("Traffic Light Turn to Green with Token {:s}".format(green_light_token))
            print("Start Flex Flow...")
            time.sleep(random.randint(10,20))
            my_traffic.release_token(green_light_token)
        else:
            print("Flow Flow Control System Traffic Light is Broken")
            print("Start Flex Flow...")
    else:
        print("Flow Flow Traffic Control System is NOT ready, bypass the Traffic Control System")
        print("Start Flex Flow...")

    return True

def fake_test():

    time.sleep(random.randint(10,20))
    print("Test Done")

if __name__ == '__main__':
    # plist = []
    # for i in range(300):
    #     p = threading.Thread(target=unitest, args=())
    #     p.daemon = True
    #     p.start()
    #     plist.append(p)
    
    # while True:
    #     if len(plist) == 0:
    #         break
    #     for thread in plist[:]:
    #         if not thread.is_alive():
    #             thread.join()
    #             plist.remove(thread)
    #     time.sleep(5)

    #sys.exit(not unitest())
    mtp_thread_list = list()
    for i in range(20):
        my_traffic = FlexFlowTrafficControl()
        green_light_token = "With Token"
        if my_traffic.is_workable():
            print("Flow Flow Traffic Control System is ready")
            green_light_token = my_traffic.is_green_light_on()
            if green_light_token:
                print("Traffic Light Turn to Green with Token {:s}".format(green_light_token))
                print("Start Flex Flow...")
            else:
                print("Flow Flow Control System Traffic Light is Broken")
                print("Start Flex Flow...")
        else:
            print("Flow Flow Traffic Control System is NOT ready, bypass the Traffic Control System")
            print("Start Flex Flow...")
        mtp_thread = threading.Thread(target = fake_test,
                                        args = ())
        mtp_thread.daemon = True
        mtp_thread.start()
        mtp_thread_list.append((mtp_thread, my_traffic, green_light_token))
        # time.sleep(1)

    # monitor all the thread
    while True:
        if len(mtp_thread_list) == 0:
            break
        for item in mtp_thread_list[:]:
            if not item[0].is_alive():
                item[0].join()
                item[1].release_token(item[2])
                mtp_thread_list.remove(item)
        time.sleep(1)
