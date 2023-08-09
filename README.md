# cs-assignment
Logic to analyze CSM bandwidth and recommend a CSM for any incoming customer based upon:
* Current portfolio bandwidth (semi-done, data dependency)
* Customer language requirements (data dependency)
* Time zone overlap (data dependency)
* Industry vertical (done)

The tool currently takes a CSV output of this report and calculates bandwidth scores for each account based upon license count + customer journey stage bandwidth impact, adds them up for each CSM, and returns a bandwidth score for each CSM. Also allows for an incoming customer's information to be entered and calculates the best CSM to partner with them.

The tool currently makes a number of assumptions for Language, Customer Journey, and Time Zone as this information is not yet captured within SFDC.

Dependencies for more accuracy:
* A "Customer Journey Stage" field at the account level in SFDC
* "Language" captured at the account/lead level
* "Time Zone" captured at the account/lead level

Other TODOs:
* Convert app entirely to client-side JS
