# Double SCTP socket buffer size`

sudo sysctl -w net.sctp.sctp_mem="40063440 53417920 80126880"
sudo sysctl -w net.sctp.sctp_rmem="32768 6924000 33554432"
sudo sysctl -w net.sctp.sctp_wmem="32768 131072 33554432"



