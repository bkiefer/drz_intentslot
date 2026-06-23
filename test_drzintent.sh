#!/bin/sh

send() {
    curl -G --data-urlencode 'text=Wassertrupp jetzt mit dem Rollschlauch zur Brandbekämpfung vorangehen!' --data-urlencode 'prev_text=Truppführer hört' 'http://localhost:5050/annotate' 2>/dev/null
}

is_alive() {
    res=`curl http://localhost:5050/alive 2>/dev/null`
    test "$res" = 'tag server is alive'
}

get_pid() {
    ps -fu kiefer | grep 'python.*adapters_bio' | grep -v grep | gawk '{ print $2 }'
}

if docker images 2>&1 | grep -q drz_daslot; then
    DOCKER_ARGS="--rm -d --name 'test_drzintent'" ./run_docker.sh >/dev/null 2>/dev/null
    until is_alive; do
        sleep 3
    done
else
    uv run adapters_bio_tags_server.py >logs/test.log 2>&1 &
    until is_alive; do
        sleep 3
    done
fi
expected='{"dialogue_act": "Einsatzbefehl", "text": "Wassertrupp jetzt mit dem Rollschlauch zur Brandbek\u00e4mpfung vorangehen!", "phrases": {"einheit": ["Wassertrupp"], "auftrag": ["mit dem Rollschlauch zur Brandbek\u00e4mpfung vorangehen"], "mittel": ["mit dem Rollschlauch"]}}'
result=$(send)
if test "$result" = "$expected"; then
    echo "Success!"
else
    echo "Failure: $result"
fi
pid=$(get_pid)
if test -n "$pid"; then
    kill -9 $pid
else
    (docker kill test_drzintent; docker container prune -f) >/dev/null 2>/dev/null
fi
