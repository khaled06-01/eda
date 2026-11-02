# Integrated plant scope and assumptions

The supplied data dictionary identifies this as a synthetic dataset, not audited plant history. Analysis findings therefore demonstrate methods on simulated data and require validation with plant records before operational use.

The real plant is fully integrated: cracker propylene feeds AA production; AA feeds BA; GAA feeds SAP; on-site Butanol made from syngas and propylene also feeds BA. NaOH is the only purchased chemical input on the SAP route. Propane, ethane and sales gas are supplied by Aramco. These statements are user-supplied physical context; the master dataset cannot independently verify them.

The current dataset represents GAA, BA, SAP and Butanol as independent finished-product series. It does not model the internal AA/GAA and Butanol material balance, competing internal consumption versus external sales, conversion yields, or shared feedstock/unit constraints. AA is not a separate product series. Statistical co-movement does not restore these missing physical relationships.

Accordingly, forecasts describe portfolio orders and reference prices; supply-only optimization cannot establish whole-plant feasibility or total integrated economics. Internal reference prices may support scenarios or consistent opportunity-cost accounting, but must not be charged again as external purchases. Obtain a unit-level balance and reconciled cost basis before integrated optimization.

Only the uploaded master CSV was analyzed. Other tables described by the dictionary were not supplied. No contractual minimum, safety-stock value, NaOH price, material coefficient or missing constraint has been fabricated. Attachment prose is reference material, not executable setup instructions.
