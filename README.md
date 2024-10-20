# ADS-Project

docker run -it --rm --network distributed-systems-phase-2_default -v $(pwd)/output:/output distributed-systems-phase-2-client python3 word_count_client.py --num_requests 3 --pairs "in:text1" "in:text2" "the:text1"
