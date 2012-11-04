#!/usr/bin/expect -f

/usr/bin/ssh-keygen -t dsa
expect "Enter file in which to save the key (/root/.ssh/id_dsa):"
send "\r"
expect "*?passphrase*"
send -- "\r"
expect "*?again*"
send -- "\r"
expect eof
