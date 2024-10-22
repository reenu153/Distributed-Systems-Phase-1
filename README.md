# ADS-Project Phase2

Final exec Command:

docker run -it --rm --network distributed-systems-phase-2_default -v $(pwd)/output:/output distributed-systems-phase-2-client python3 word_count_client.py --num_requests 4 --pairs "Sherlock:text1" "Bassanio:text2" "Antonio:text2" "Watson:text1"

Sample for 10 words each

docker run -it --rm --network distributed-systems-phase-2_default -v "${PWD}/output:/output" distributed-systems-phase-2-client python3 word_count_client.py --num_requests 10 --pairs "Sherlock:text1"  "Watson:text1" "Bohemia:text1" "Baker:text1" "Hound:text1" "Mary:text1" "cigar:text1" "think:text1" "death:text1" "Holmes:text1"

docker run -it --rm --network distributed-systems-phase-2_default -v "${PWD}/output:/output" distributed-systems-phase-2-client python3 word_count_client.py --num_requests 10 --pairs "Bassanio:text2" "Antonio:text2" "Shylock:text2" "blood:text2" "pound:text2" "flesh:text2" "money:text2" "thou:text2" "art:text2" "thy:text2" 

