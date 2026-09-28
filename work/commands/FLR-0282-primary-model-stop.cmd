if test -r /run/user/1001/flr0282-primary-model.pid; then pid=$(cat /run/user/1001/flr0282-primary-model.pid); kill -TERM "$pid" 2>/dev/null || true; fi; printf 'FLR0282_PRIMARY_MODEL_STOP_DONE\n'
