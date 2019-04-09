
# Given alpha the threshold required for different sample size s
library("TailRank")

single_proba <- function(s, n, a=1, b=1, risk=0.1, h0_p=0.5, approximation=FALSE) {
    if (!approximation) {
        sa = qbinom(1 - risk, s, h0_p)
    } else {
        sa = qnorm(1 - risk, mean=s * h0_p, sd= sqrt(s * h0_p *  (1 - h0_p)))
    }
    # Return P(X > n/2 - sa | sa+a, sb+b) = 1 - P(X <= n/2 - sa | sa+a, sb+b)
    return(1 - pbb(n/2 - sa, n - s, sa+a, s-sa+b))
}

n = 100000
risk = 0.05
a = 1
b = 1
approximation = TRUE
ss = 1:5000
h0_p = 0.5
probas = c()
for (s in ss) {
    probas[s] <- single_proba(s, n, a=a, b=b, risk=risk, h0_p=h0_p, approximation=approximation)
}
plot(ss, probas, type="l")
print(probas)

n = 100000
risk = 0.05
a = 1
b = 1
approximation = FALSE
ss = 1:5000
h0_p = 0.5
probas = c()
for (s in ss) {
    probas[s] <- single_proba(s, n, a=a, b=b, risk=risk, h0_p=h0_p, approximation=approximation)
}
plot(ss, probas, type="l")
print(probas)

check_rejection <- function(sample_winner, sample_loser, n, a, b, thresh=0.95, return_prob=FALSE) {
    p_win = 1 - pbb(n/2-sample_winner, n - sample_winner - sample_loser, sample_winner+a, sample_loser+b)
    if (return_prob) {
        return(p_win)
    }
    return(p_win >= thresh)
}

#' Try to simulate the random walk of a two candidate election auditing process.
#' Need to specify either
#'     - m: The number of votes till stopping
#'     - replacement: False -> to go for a full audit
#' The auditing will not stop until
#'     - The winner is declared winning
#'     - The audit reached threshold m (default to n)
#'     - Input didn't meet above condition
#' The simulation will return
#'     - The number of ballot drawn (1 to m)
rw_simulation <- function(n, m, step=1, a=1, b=1, thresh=0.95, risk=0.1, h1_p=0.6, 
                          h0_p=0.5, replacement=TRUE, show_walk=FALSE) {
    s = 0
    if (m == -1 && replacement) {
        return(0)
    } else if (m == -1) {
        m = n
    }
    vote_winner = n * h1_p
    vote_loser = n * (1-h1_p)
    
    sample_winner = 0
    sample_loser = 0
    walk = c()
    while (s < m) {
        # Advance the counter
        s = s + step
        # Sample a batch of votes
        batch = rbinom(1, step, vote_winner/(vote_loser+vote_winner))
        if (!replacement) {
            # If no replacement then remove those votes from poll
            vote_winner = vote_winner - batch
            vote_loser = vote_loser - (step - batch)
        }
        sample_winner = sample_winner + batch
        sample_loser = sample_loser + (step - batch)
        walk = c(walk, sample_winner, sample_loser)
        
        # If rejected null hypothesis (or accepted the alternative hypothesis)
        if (check_rejection(sample_winner, sample_loser, n, a, b, thresh)) {
            if (show_walk) {
                return(list(s=s, walk=matrix(walk, nrow=2)))
            }
            return(s)
        }
    }
    return(s)
}

total = 0
no_stop = 0
times = 100
stop = 3000
for (i in 1:times) {
    s = rw_simulation(100000, stop, h1_p=0.51, replacement=TRUE)
    total = total + s
    if (s >= stop) {
        no_stop = no_stop + 1
    }
}
c(total / times, no_stop)
