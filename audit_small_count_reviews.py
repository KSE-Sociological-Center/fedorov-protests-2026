"""Manual context verdicts for passages added by the spelled-small-number screen."""

# Keys are (source_id, zero-based paragraph index in the normalized body).
REVIEWS = {
    ("0cedd9e24504608c93ec", 13): ("rejected_non_turnout", "Hypothetical two people meeting in a cabinet; not a protest count."),
    ("27066793a757f633b6b1", 8): ("rejected_single_interviewee", "The phrase identifies one quoted participant, not total attendance."),
    ("4e87e6efe57f29aa6a9e", 4): ("verified_turnout", "Literal Mykolaiv 4 August turnout of nine; already selected in the daily ledger."),
    ("4f79ad5329b11a967334", 5): ("rejected_non_turnout", "One additional fulfilled demand, not a person count."),
    ("536c4ff44999b81729a0", 19): ("rejected_single_interviewee", "Introduces one interviewee; not total attendance."),
    ("53ce8175c5f73e00265a", 35): ("rejected_single_interviewee", "Introduces one interviewee; not total attendance."),
    ("5c1588604432b30025cb", 11): ("verified_relay", "Literal Mykolaiv 5 August count of seven in an AMP-equivalent relay; kept only as alternative evidence."),
    ("62f950baabc74fccd867", 23): ("rejected_single_interviewee", "Introduces one interviewee; not total attendance."),
    ("6710c490ad0af5e901e3", 14): ("rejected_non_turnout", "One fulfilled demand, not a person count."),
    ("6d862700f472f31d3a2d", 42): ("rejected_single_interviewee", "Introduces one interviewee; not total attendance."),
    ("77767f15180422ee3cea", 13): ("rejected_hypothetical", "A participant's hypothetical 'even one person' statement, not observed turnout."),
    ("87260944ee9d63de394b", 4): ("verified_alternative", "Literal Mykolaiv 5 August count of seven; retained as the documented alternative to the selected count of eight."),
    ("8d4242a7e885dbccfdcc", 15): ("rejected_non_turnout", "Three to four evacuation personnel in a military example; not protesters."),
    ("93740036fe267d59edd3", 8): ("rejected_single_interviewee", "Introduces one interviewee; not total attendance."),
    ("a02e6282bc6a6d323a89", 2): ("verified_initial_snapshot", "Literal initial Zhytomyr 28 July snapshot of two; later arrivals are unquantified."),
    ("a02e6282bc6a6d323a89", 5): ("rejected_single_interviewee", "Introduces one interviewee; not total attendance."),
    ("af7f53243c65f450e852", 8): ("rejected_single_interviewee", "Introduces one interviewee; not total attendance."),
    ("af7f53243c65f450e852", 14): ("rejected_single_interviewee", "Introduces one interviewee; not total attendance."),
    ("b4a5ca1cc117bb846cf3", 13): ("verified_relay", "Literal relay of the initial Zhytomyr 28 July snapshot of two; later arrivals are unquantified."),
    ("cc171d96b08c4b1a2fe1", 6): ("rejected_single_interviewee", "Introduces one interviewee; not total attendance."),
    ("d2ddb83db8914581122f", 2): ("rejected_non_turnout", "One fulfilled demand, not a person count."),
    ("e52dc6cd3d4b4bb34260", 8): ("verified_turnout", "Literal Mykolaiv 5 August turnout of eight; selected over the seven-person relay."),
    ("f84ea2afe37d851222ce", 2): ("rejected_non_turnout", "One fulfilled demand, not a person count."),
}

