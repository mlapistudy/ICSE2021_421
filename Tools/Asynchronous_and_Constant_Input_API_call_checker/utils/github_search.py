import sys
import os
import github
from time import sleep
import time
from datetime import datetime, date

# Register using different credentials to maximize rate limit
g1 = github.Github("your-token")
g2 = github.Github("your-token")
g3 = github.Github("your-token")

using = 1
SLEEP_TIME = 15

def swap_g():
    global g1
    global g2
    global g3
    global using
    if using == 1:
        print("Network exception triggered, changing from g1 to g2, value of using before change: {}".format(using))
        sleep(SLEEP_TIME)
        using = 2
        return g2
    elif using == 2:
        print("Network exception triggered, changing from g2 to g3, value of using before change: {}".format(using))
        sleep(SLEEP_TIME)
        using = 3
        return g3
    elif using == 3:
        print("Network exception triggered, changing from g3 to g1, value of using before change: {}".format(using))
        sleep(SLEEP_TIME)
        using = 1
        return g1


def search_github(keyword, repo, out_fd):
    # Initialize as g1
    g = g3
    global using
    
    # rate = g.get_rate_limit().search
    # if rate.remaining == 0:
    #     print('You have 0/{} API calls remaining. Reset time: {}'.format(rate.limit, rate.reset))
    #     sleep(60)
    # else:
    # print('You have {}/{} API calls remaining'.format(rate.remaining, rate.limit))    
    print_writeofd("Searching repo: {} for keyword: {}".format(repo, keyword), out_fd)
    query = "{} repo:{} language:Python".format(keyword, repo)
    changed = 0
    while True:
        try:
            result = g.search_code(query, order='desc')

            total_count = result.totalCount
            max_size = 100
            print_writeofd('Found {} file(s)'.format(total_count), out_fd)
            if total_count > max_size:
                result = result[:max_size]
        
            download_url = []
            for file in result:
                download_url.append(file.download_url)
            
            changed = 0

        except github.RateLimitExceededException as e:
            if changed == 0:
                g = swap_g()
                changed = 1
                continue
            elif changed == 1:
                start = datetime.now().time()
                end = datetime.now().time()
                while (datetime.combine(date.min, end) - datetime.combine(date.min, start)).total_seconds() < 120:
                    time_elapsed = (datetime.combine(date.min, end) - datetime.combine(date.min, start)).total_seconds()
                    progress(time_elapsed, 120)
                    sleep(2)
                    end = datetime.now().time()
                print("")
                continue
        except github.GithubException as e:
            print_writeofd("Other Github Exceptions occurred: {}\n".format(e), out_fd)
            return None
        return download_url

def progress(i, j):
    sys.stdout.write("\rRate Limit Hit, waiting for %i seconds. Already waited %i" % (j, i))
    sys.stdout.flush()

def print_writeofd(string, ofd):
    print(string)
    ofd.write(string + "\n")

