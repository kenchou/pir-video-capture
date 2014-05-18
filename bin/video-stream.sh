#!/bin/bash
raspivid -n -ex auto -t 0 -fps 25 -b 1000000 -w 1024 -h 576 -o - | cvlc stream:///dev/stdin --sout "#standard{access=http{$1},mux=ts,dst=:8554}" :demux=h264
