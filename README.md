# narwhal

A pre-fork worker model Python HTTP server based on the ideas and techniques used in [unicorn](https://bogomips.org/unicorn/) and it's Python port [Gunicorn](https://github.com/benoitc/gunicorn).

This is a learning exercise and not intend to be useful as standalone software. I am working on a potential blog post and hope this source will be a useful reference for others eventually.

## Usage

There are no external dependencies, you only need to have Python3 installed.
```
$ ./narwhal.py --help

usage: narwhal.py [-h] [-w WORKER_COUNT] [-p PORT] [-d]

Run a pre-fork worker HTTP server

optional arguments:
  -h, --help            show this help message and exit
  -w WORKER_COUNT, --worker_count WORKER_COUNT
                        The number of workers processes to run
  -p PORT, --port PORT  The port to listen for requests on
  -d, --debug           If set enables debug level logs
```

Once running you can access `localhost:8080` (default port) in your browser, or via `curl`.

## Performance

Some quick benchmarking using [Siege](https://www.joedog.org/siege-manual/) showed great performance:
```
Transactions:		       10000 hits
Availability:		      100.00 %
Elapsed time:		        7.94 secs
Data transferred:	        0.31 MB
Response time:		        0.08 secs
Transaction rate:	     1259.45 trans/sec
Throughput:		        0.04 MB/sec
Concurrency:		       94.59
Successful transactions:       10000
Failed transactions:	           0
Longest transaction:	        0.33
Shortest transaction:	        0.01
```
