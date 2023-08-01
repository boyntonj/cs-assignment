# cs-assignment
Logic to analyze CSM bandwidth and recommend a CSM for any incoming customer based upon:
* Current portfolio bandwidth (semi-done, data dependency)
* Customer language requirements (data dependency)
* Time zone overlap (data dependency)
* Industry vertical (done)

App currently takes a CSV output of this report and calculates bandwidth scores for each account based upon license count + customer journey stage bandwidth impact, adds them up for each CSM, and returns a bandwidth score.

It currently assumes that all customers are in the same stage of the journey (Onboarding), as we don't have a place to capture that data in SFDC at this point.

Dependencies for more accuracy:
* A "Customer Journey Stage" field at the account level in SFDC
* "Language" captured at the account/lead level
* "Time Zone" captured at the account/lead level
