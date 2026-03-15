##############################################################################
# validate_nma_bayesian.R
#
# Bayesian NMA validation using gemtc + JAGS.
#
# *** PLACEHOLDER *** — requires JAGS to be installed on the system.
# Download JAGS from: https://sourceforge.net/projects/mcmc-jags/
#
# This script would:
#   1. Load the smokingcessation data and synthetic datasets
#   2. Convert contrast-level data to arm-level format for gemtc
#   3. Run Bayesian NMA via gemtc::mtc.model() + mtc.run()
#   4. Extract posterior medians, 95% CrI, SUCRA, DIC
#   5. Export to bayesian_reference.json
#
# Requirements:
#   install.packages(c("gemtc", "rjags", "coda", "jsonlite"))
#   JAGS must be installed separately (not an R package)
#
# Usage:
#   Rscript R_validation/validate_nma_bayesian.R
#
# Output:
#   R_validation/bayesian_reference.json
##############################################################################

suppressPackageStartupMessages({
  library(jsonlite)
})

cat("=== MetaSprint NMA Canonical Validation (Bayesian) ===\n")
cat(sprintf("  R version : %s\n", R.version.string))
cat(sprintf("  Date      : %s\n", Sys.time()))
cat("=====================================================\n\n")

# ── Check if gemtc and rjags are available ────────────────────────────────────
gemtc_available <- requireNamespace("gemtc", quietly = TRUE)
rjags_available <- requireNamespace("rjags", quietly = TRUE)

if (!gemtc_available || !rjags_available) {
  cat("WARNING: gemtc and/or rjags not installed.\n")
  cat("  gemtc available: ", gemtc_available, "\n")
  cat("  rjags available: ", rjags_available, "\n")
  cat("\nTo install:\n")
  cat("  1. Install JAGS: https://sourceforge.net/projects/mcmc-jags/\n")
  cat("  2. install.packages(c('rjags', 'gemtc'))\n")
  cat("\nGenerating placeholder bayesian_reference.json...\n")

  placeholder <- list(
    schema  = "bayesian_reference.v1",
    created = as.character(Sys.time()),
    status  = "placeholder",
    reason  = "gemtc/rjags/JAGS not available on this system",
    note    = paste("Install JAGS and R packages gemtc + rjags,",
                    "then re-run this script to generate actual Bayesian reference values."),
    datasets = list(
      smoking     = NULL,
      oncology_hr = NULL,
      minimal     = NULL,
      high_het    = NULL,
      multiarm    = NULL
    )
  )

  out_path <- file.path("R_validation", "bayesian_reference.json")
  writeLines(toJSON(placeholder, pretty = TRUE, auto_unbox = TRUE, na = "null"),
             out_path)
  cat(sprintf("Wrote placeholder: %s\n", out_path))
  cat("Done (placeholder only).\n")
  quit(save = "no", status = 0)
}

# ── If we reach here, gemtc + rjags are available ────────────────────────────
library(gemtc)
library(rjags)
library(coda)

cat(sprintf("  gemtc version: %s\n", packageVersion("gemtc")))
cat(sprintf("  rjags version: %s\n", packageVersion("rjags")))
cat("\n")


# ── Helper: run gemtc Bayesian NMA on contrast-level data ────────────────────
#
# gemtc expects arm-level data (treatment, study, responders, sampleSize) for
# binary outcomes, or contrast-level data (diff, std.err) for relative effects.
#
# For contrast-level input, we use mtc.network() with data.re (relative effect).
#
# Arguments:
#   dat        - data.frame with columns: study, t1, t2, TE, seTE
#   sm         - summary measure label
#   dataset_id - string identifier
#   n_adapt    - adaptation iterations (default 5000)
#   n_iter     - sampling iterations (default 20000)
#   n_thin     - thinning (default 10)
#
# Returns a named list with posterior summaries.
run_bayesian_nma <- function(dat, sm, dataset_id,
                             n_adapt = 5000, n_iter = 20000, n_thin = 10) {
  cat(sprintf("── Bayesian NMA: %s ──\n", dataset_id))

  # Convert to gemtc relative-effect format
  # gemtc data.re requires: study, treatment, diff, std.err
  # For multi-arm, one arm per study is the baseline (diff=NA, std.err=NA)
  # For contrast-level data, we build the data.re frame manually.

  # Get unique studies and their treatments
  studies <- unique(dat$study)
  treatments <- sort(unique(c(dat$t1, dat$t2)))

  # Build data.re: each study contributes (k-1) rows for k arms
  # t2 is the baseline arm within each contrast
  re_rows <- list()
  for (s in studies) {
    sdat <- dat[dat$study == s, ]
    # Identify baseline treatment for this study (the common t2)
    baseline <- unique(sdat$t2)
    if (length(baseline) > 1) {
      # Multi-arm: pick the most common t2 as baseline
      baseline <- names(sort(table(sdat$t2), decreasing = TRUE))[1]
    }

    # Add baseline row (no diff)
    re_rows[[length(re_rows) + 1]] <- data.frame(
      study     = s,
      treatment = baseline,
      diff      = NA,
      std.err   = NA,
      stringsAsFactors = FALSE
    )

    # Add contrast rows
    for (r in seq_len(nrow(sdat))) {
      if (sdat$t2[r] == baseline) {
        re_rows[[length(re_rows) + 1]] <- data.frame(
          study     = s,
          treatment = sdat$t1[r],
          diff      = sdat$TE[r],
          std.err   = sdat$seTE[r],
          stringsAsFactors = FALSE
        )
      }
    }
  }
  data_re <- do.call(rbind, re_rows)

  cat(sprintf("  Prepared %d rows for %d studies, %d treatments\n",
              nrow(data_re), length(studies), length(treatments)))

  # Create network
  network <- mtc.network(data.re = data_re)

  # Create model (random effects, normal likelihood for relative effects)
  model <- mtc.model(network,
                     linearModel = "random",
                     n.chain = 4,
                     likelihood = "normal",
                     link = "identity")

  # Run MCMC
  cat(sprintf("  Running MCMC: %d adapt + %d iter (thin=%d), 4 chains...\n",
              n_adapt, n_iter, n_thin))
  result <- mtc.run(model,
                    n.adapt = n_adapt,
                    n.iter  = n_iter,
                    thin    = n_thin)

  # Check convergence (Gelman-Rubin)
  gr <- gelman.diag(result, multivariate = FALSE)
  max_psrf <- max(gr$psrf[, "Point est."])
  cat(sprintf("  Max Gelman-Rubin PSRF: %.3f %s\n",
              max_psrf, if (max_psrf < 1.05) "(CONVERGED)" else "(WARNING: not converged)"))

  # Extract summaries
  smry <- summary(result)
  stats <- smry$statistics
  quants <- smry$quantiles

  # Treatment effects (d.X.Y = X vs Y on the link scale)
  d_params <- grep("^d\\.", rownames(stats), value = TRUE)

  effects <- list()
  for (p in d_params) {
    effects[[p]] <- list(
      mean   = stats[p, "Mean"],
      sd     = stats[p, "SD"],
      median = quants[p, "50%"],
      lower  = quants[p, "2.5%"],
      upper  = quants[p, "97.5%"]
    )
  }

  # SUCRA (Surface Under the Cumulative Ranking curve)
  cat("  Computing SUCRA...\n")
  ranks <- rank.probability(result)
  sucra <- list()
  rank_probs <- as.matrix(ranks)
  n_trt <- ncol(rank_probs)
  for (i in seq_len(nrow(rank_probs))) {
    trt_name <- rownames(rank_probs)[i]
    cum_prob <- cumsum(rank_probs[i, ])
    sucra_val <- sum(cum_prob[-n_trt]) / (n_trt - 1)
    sucra[[trt_name]] <- sucra_val
  }

  # DIC
  dic_val <- tryCatch(summary(result)$DIC, error = function(e) NA)

  # tau (between-study SD)
  tau_row <- grep("^sd\\.d$", rownames(stats), value = TRUE)
  tau_summary <- if (length(tau_row) > 0) {
    list(
      mean   = stats[tau_row, "Mean"],
      median = quants[tau_row, "50%"],
      lower  = quants[tau_row, "2.5%"],
      upper  = quants[tau_row, "97.5%"]
    )
  } else {
    NULL
  }

  output <- list(
    dataset    = dataset_id,
    n_chains   = 4,
    n_adapt    = n_adapt,
    n_iter     = n_iter,
    n_thin     = n_thin,
    max_psrf   = max_psrf,
    converged  = max_psrf < 1.05,
    effects    = effects,
    sucra      = sucra,
    rank_probs = as.data.frame(rank_probs),
    tau        = tau_summary,
    dic        = dic_val
  )

  cat(sprintf("  Done: %s (SUCRA computed for %d treatments)\n\n",
              dataset_id, length(sucra)))
  return(output)
}


# ══════════════════════════════════════════════════════════════════════════════
# RUN ALL 5 DATASETS
# ══════════════════════════════════════════════════════════════════════════════

# Dataset 1: Smoking Cessation
data(smokingcessation, package = "netmeta")
smoking_es <- metafor::escalc(measure = "OR",
                              ai = smokingcessation$event1,
                              n1i = smokingcessation$n1,
                              ci = smokingcessation$event2,
                              n2i = smokingcessation$n2,
                              data = smokingcessation)
smoking_dat <- data.frame(
  study = smokingcessation$studlab,
  t1    = as.character(smokingcessation$treat1),
  t2    = as.character(smokingcessation$treat2),
  TE    = as.numeric(smoking_es$yi),
  seTE  = sqrt(as.numeric(smoking_es$vi)),
  stringsAsFactors = FALSE
)
smoking_bayes <- run_bayesian_nma(smoking_dat, "OR", "smoking")

# Dataset 2: CKD Nephroprotection (oncology_hr)
oncology_dat <- data.frame(
  study = c("CREDENCE", "DAPA-CKD", "EMPA-KIDNEY", "FIDELIO-DKD", "FIGARO-DKD"),
  t1    = c("Canagliflozin", "Dapagliflozin", "Empagliflozin", "Finerenone", "Finerenone"),
  t2    = rep("Placebo", 5),
  TE    = c(-0.3567, -0.4943, -0.3285, -0.1985, -0.1278),
  seTE  = c(0.0847, 0.0882, 0.0639, 0.0617, 0.0857),
  stringsAsFactors = FALSE
)
oncology_bayes <- run_bayesian_nma(oncology_dat, "HR", "oncology_hr")

# Dataset 3: Minimal
minimal_dat <- data.frame(
  study = c("S1", "S2", "S3"),
  t1    = rep("Treatment", 3),
  t2    = rep("Control", 3),
  TE    = c(0.50, 0.55, 0.48),
  seTE  = c(0.25, 0.30, 0.28),
  stringsAsFactors = FALSE
)
minimal_bayes <- run_bayesian_nma(minimal_dat, "OR", "minimal")

# Dataset 4: High Heterogeneity
high_het_dat <- data.frame(
  study = c("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"),
  t1    = c("A", "A", "A", "B", "B", "B", "A", "A"),
  t2    = c("C", "C", "C", "C", "C", "C", "B", "B"),
  TE    = c(1.2, 0.2, 0.8, 0.5, -0.3, 1.1, 0.4, 0.1),
  seTE  = c(0.3, 0.25, 0.35, 0.4, 0.3, 0.28, 0.32, 0.38),
  stringsAsFactors = FALSE
)
high_het_bayes <- run_bayesian_nma(high_het_dat, "OR", "high_het")

# Dataset 5: Multi-arm
multiarm_dat <- data.frame(
  study = c("MA1", "MA1", "MA1", "MA2", "MA2", "MA2"),
  t1    = c("A", "B", "A", "B", "C", "B"),
  t2    = c("D", "D", "B", "D", "D", "C"),
  TE    = c(0.6, 0.3, 0.3, 0.4, 0.7, -0.3),
  seTE  = c(0.25, 0.28, 0.30, 0.22, 0.26, 0.24),
  stringsAsFactors = FALSE
)
multiarm_bayes <- run_bayesian_nma(multiarm_dat, "OR", "multiarm")


# ══════════════════════════════════════════════════════════════════════════════
# ASSEMBLE AND EXPORT
# ══════════════════════════════════════════════════════════════════════════════
output <- list(
  schema  = "bayesian_reference.v1",
  created = as.character(Sys.time()),
  status  = "computed",
  R_version = R.version.string,
  packages = list(
    gemtc  = as.character(packageVersion("gemtc")),
    rjags  = as.character(packageVersion("rjags")),
    jsonlite = as.character(packageVersion("jsonlite"))
  ),
  mcmc_settings = list(
    n_chains = 4,
    n_adapt  = 5000,
    n_iter   = 20000,
    n_thin   = 10
  ),
  datasets = list(
    smoking     = smoking_bayes,
    oncology_hr = oncology_bayes,
    minimal     = minimal_bayes,
    high_het    = high_het_bayes,
    multiarm    = multiarm_bayes
  )
)

out_path <- file.path("R_validation", "bayesian_reference.json")
json_str <- toJSON(output, pretty = TRUE, auto_unbox = TRUE, na = "null",
                   digits = 8, force = TRUE)
writeLines(json_str, out_path)

cat(sprintf("\n=== DONE: wrote %s (%d bytes) ===\n",
            out_path, file.size(out_path)))
cat("All Bayesian reference values exported successfully.\n")
