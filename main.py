# main
import getopt
import sys
import logging
import time
from threading import Thread, Event
from queue import Queue
from binance.client import Client
from docs.conf import *
from docs.botconf import *
import app, app.bot

##### Globals #####
log = logging.getLogger('main')
divstr = "***** %s *****"
# Candle data queue. Feeder is bot.websock, consumer is bot.trade
q = Queue()
# Enabled pair change event
e_pairs = Event()
# Thread termination event
e_kill = Event()

if __name__ == '__main__':
    killer = app.GracefulKiller()
    app.set_db(host)
    app.bot.init()

    from app.bot import candles, scanner, trade, websock

    # Handle input commands
    try:
        opts, args = getopt.getopt(sys.argv[1:], ":c", ['candles'])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt not in('-c', '--candles'):
            continue
        #pairs = app.bot.get_pairs()

    # Create worker threads. Set as daemons so they terminate
    # automatically if main process is killed.
    threads = []
    for func in [websock.run, trade.run, scanner.run]:
        threads.append(Thread(
            name='{}.{}'.format(func.__module__, func.__name__),
            target=func,
            args=(e_pairs, e_kill,)
        ))
        threads[-1].setDaemon(True)
        threads[-1].start()

    # Main loop. Monitors threads and terminates app on CTRL+C cmd.
    while True:
        if killer.kill_now:
            e_kill.set()
            break
        for t in threads:
            if t.is_alive() == False:
                print("Thread {} is dead!".format(t.getName()))
                time.sleep(1)
        time.sleep(0.1)

    # Wait for trade & websock threads to close.
    # Scanner sleep period too long to wait.
    threads[0].join()
    threads[1].join()

    print("Goodbye")
    log.debug(divstr % "sys.exit()")
    log.info(divstr % "Terminating")
    sys.exit()
