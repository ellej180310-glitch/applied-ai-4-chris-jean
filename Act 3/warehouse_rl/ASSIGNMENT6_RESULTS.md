# Assignment 6: Advanced Optimization Results

## Performance Summary

| Test stage | Episodes | Placement | Average profit | 95% confidence interval | Completion rate |
|---|---:|---:|---:|---:|---:|
| Initial benchmark | 10 | 8th of 8 | $1,102.78 | ±$1,460.30 | 25.4% ± 2.1% |
| Staffing test | 3 | Not ranked | $24,487.72 | Not calculated | 49.5% average |
| Integrated staffing and routing test | 5 | Not ranked | $25,433.22 | Not calculated | 50.9% average |
| Final benchmark | 10 | 1st of 8 | $27,069.67 | ±$4,005.85 | 58.9% ± 5.9% |

The final agent improved its average profit by $25,966.89 and moved from eighth place to first place. Its completion rate increased by 33.5 percentage points. The approximate initial profit interval was -$357.52 to $2,563.08, while the final interval was $23,063.82 to $31,075.52. Because these intervals do not overlap, the final improvement was much larger than the uncertainty shown by the benchmark. However, the final interval was still relatively wide, showing that performance varied across episodes.

## Iterative Improvement Process

The initial benchmark was run before implementing the Assignment 6 staffing and routing changes. It showed that the agent’s existing layout strategy was not enough by itself because random staffing and order assignments limited warehouse capacity.

The staffing-only test used three episodes. Its profits were $21,615.76, $25,166.29, and $26,681.11, producing an average of $24,487.72. This demonstrated that demand-based staffing made the largest immediate improvement.

The five-episode integration test evaluated staffing, routing, and layout together. Its profits were $26,243.99, $24,391.29, $24,181.78, $26,251.34, and $26,097.68. The average profit was $25,433.22, approximately $945.50 higher than the staffing-only average. The final ten-episode benchmark was then used for the official comparison.

## Optimization Strategies

### Staffing

The staffing algorithm reviews demand and financial conditions at controlled intervals. It measures queue pressure, profit, revenue, burn rate, workforce size, and recent profit movement. Workers are hired when order demand exceeds available capacity and the warehouse can afford the additional wage. Workers are fired only when demand is low, financial pressure exists, and minimum staffing requirements are protected. Separate hiring and firing thresholds create a buffer that prevents rapid switching between the two decisions. The algorithm also maintains one manager when the warehouse is profitable enough to support layout optimization without paying for unnecessary additional managers.

### Routing

The routing algorithm identifies idle non-manager workers and pending orders. It scores each worker-order combination using walking distance, order value, waiting time, priority, and deadline urgency. Distance receives 70% of the base score and value receives 30%, followed by an urgency adjustment. The Hungarian assignment algorithm then selects the combination of worker-order matches with the greatest total benefit while ensuring that each worker and order is used at most once.

### Layout Integration

The existing layout strategy moves frequently requested products closer to the truck bays and groups products that frequently appear in the same orders. Layout changes are requested only when the queue is manageable and an idle manager is available. Staffing provides enough workers to process demand while preserving a manager for useful relocations. The improved layout then reduces the distances used by the routing algorithm, while routing keeps workers productive enough to justify the staffing cost.

## Multi-Objective Trade-offs

The agent balances profit, service speed, labor cost, relocation cost, and employee utilization. Hiring more workers improves processing capacity but raises the warehouse burn rate. Hiring a manager supports layout optimization but costs more than hiring a regular worker. Assigning only the nearest order reduces walking distance, but it can delay more valuable or urgent orders. Frequent layout changes may reduce future retrieval distance, but they temporarily occupy the manager. The coordinated strategy uses thresholds and weighted assignment scores to balance these competing objectives instead of optimizing only one measurement.