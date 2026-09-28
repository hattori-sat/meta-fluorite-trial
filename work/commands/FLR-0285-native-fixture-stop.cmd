if test -r /run/user/1001/flr0285-native-fixture.pid; then pid=$(cat /run/user/1001/flr0285-native-fixture.pid); kill -TERM "$pid" 2>/dev/null || true; fi; printf 'FLR0285_NATIVE_FIXTURE_STOP_DONE\n'
