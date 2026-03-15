##############################################################################
# validate_nma_netmeta.R
#
# Canonical NMA validation using the netmeta R package.
# Runs 5 datasets (1 real + 4 synthetic) through netmeta with DL and REML,
# extracts treatment effects, heterogeneity, P-scores, node-splitting,
# HKSJ adjustment, and prediction intervals, then exports everything to
# frequentist_reference.json for comparison with the MetaSprint NMA WebR engine.
#
# Requirements:
#   install.packages(c("netmeta", "metafor", "jsonlite"))
#
# Usage:
#   Rscript R_validation/validate_nma_netmeta.R
#
# Output:
#   R_validation/frequentist_reference.json
##############################################################################

# ── Load packages ─────────────────────────────────────────────────────────────
suppressPackageStartupMessages({
  library(netmeta)
  library(metafor)
  library(jsonlite)
})

cat("=== MetaSprint NMA Canonical Validation (Frequentist) ===\n")
cat(sprintf("  R version      : %s\n", R.version.string))
cat(sprintf("  netmeta version: %s\n", packageVersion("netmeta")))
cat(sprintf("  metafor version: %s\n", packageVersion("metafor")))
cat(sprintf("  jsonlite version: %s\n", packageVersion("jsonlite")))
cat(sprintf("  Date           : %s\n", Sys.time()))
cat("==========================================================\n\n")


# ── Helper: run full netmeta analysis on a contrast-level dataset ─────────────
#
# Arguments:
#   dat        - data.frame with columns: study, t1, t2, TE, seTE
#   sm         - summary measure label ("OR", "HR", etc.)
#   reference  - reference treatment name
#   dataset_id - string identifier for output
#
# Returns a named list with all extracted results.
run_netmeta_analysis <- function(dat, sm, reference, dataset_id) {
  cat(sprintf("── Dataset: %s (%d contrasts, ref='%s', sm='%s') ──\n",
              dataset_id, nrow(dat), reference, sm))

  results <- list(
    dataset   = dataset_id,
    sm        = sm,
    reference = reference,
    n_studies = length(unique(dat$study)),
    n_contrasts = nrow(dat),
    treatments = NULL,
    dl  = list(),
    reml = list(),
    hksj = list(),
    node_splitting = list()
  )

  # ── DerSimonian-Laird ────────────────────────────────────────────────────
  cat("  Running netmeta (DL)...\n")
  net_dl <- tryCatch(
    netmeta(TE = dat$TE, seTE = dat$seTE,
            treat1 = dat$t1, treat2 = dat$t2,
            studlab = dat$study,
            sm = sm, reference.group = reference,
            method.tau = "DL",
            comb.fixed = TRUE, comb.random = TRUE),
    error = function(e) {
      # netmeta >= 7.0 uses "common" instead of "comb.fixed"
      netmeta(TE = dat$TE, seTE = dat$seTE,
              treat1 = dat$t1, treat2 = dat$t2,
              studlab = dat$study,
              sm = sm, reference.group = reference,
              method.tau = "DL",
              common = TRUE, random = TRUE)
    }
  )

  treatments <- sort(net_dl$trts)
  results$treatments <- treatments
  n_trt <- length(treatments)

  # Extract treatment effect matrix (random effects)
  te_random_dl <- matrix(NA, nrow = n_trt, ncol = n_trt,
                         dimnames = list(treatments, treatments))
  se_random_dl <- te_random_dl
  lower_random_dl <- te_random_dl
  upper_random_dl <- te_random_dl
  lower_predict_dl <- te_random_dl
  upper_predict_dl <- te_random_dl

  for (i in seq_along(treatments)) {
    for (j in seq_along(treatments)) {
      if (i != j) {
        ti <- treatments[i]
        tj <- treatments[j]
        te_random_dl[ti, tj]    <- net_dl$TE.random[ti, tj]
        se_random_dl[ti, tj]    <- net_dl$seTE.random[ti, tj]
        lower_random_dl[ti, tj] <- net_dl$lower.random[ti, tj]
        upper_random_dl[ti, tj] <- net_dl$upper.random[ti, tj]
        # Prediction intervals (may not exist in all netmeta versions)
        if (!is.null(net_dl$lower.predict)) {
          lower_predict_dl[ti, tj] <- net_dl$lower.predict[ti, tj]
          upper_predict_dl[ti, tj] <- net_dl$upper.predict[ti, tj]
        }
      }
    }
  }

  # Heterogeneity
  tau2_dl <- net_dl$tau^2
  I2_dl   <- if (!is.null(net_dl$I2)) net_dl$I2 * 100 else NA
  Q_dl    <- if (!is.null(net_dl$Q)) net_dl$Q else NA
  Q_df    <- if (!is.null(net_dl$df.Q)) net_dl$df.Q else NA
  Q_pval  <- if (!is.null(net_dl$pval.Q)) net_dl$pval.Q else NA

  # P-scores (random effects)
  cat("  Computing P-scores (DL)...\n")
  rank_dl <- tryCatch(
    netrank(net_dl, small.values = if (sm == "HR") "good" else "bad"),
    error = function(e) {
      cat(sprintf("    Warning: netrank failed: %s\n", e$message))
      NULL
    }
  )
  pscores_dl <- if (!is.null(rank_dl)) {
    # netrank returns Pscore.random or ranking.random depending on version
    if (!is.null(rank_dl$Pscore.random)) {
      as.list(rank_dl$Pscore.random)
    } else if (!is.null(rank_dl$ranking.random)) {
      as.list(rank_dl$ranking.random)
    } else {
      NULL
    }
  } else {
    NULL
  }

  results$dl <- list(
    tau2  = tau2_dl,
    tau   = net_dl$tau,
    I2    = I2_dl,
    Q     = Q_dl,
    Q_df  = Q_df,
    Q_pval = Q_pval,
    TE_random  = as.data.frame(te_random_dl),
    seTE_random = as.data.frame(se_random_dl),
    lower_random = as.data.frame(lower_random_dl),
    upper_random = as.data.frame(upper_random_dl),
    lower_predict = as.data.frame(lower_predict_dl),
    upper_predict = as.data.frame(upper_predict_dl),
    pscores = pscores_dl
  )

  cat(sprintf("  DL: tau2=%.6f, I2=%.1f%%, Q=%.4f (df=%d, p=%.4f)\n",
              tau2_dl, I2_dl, Q_dl, Q_df, Q_pval))

  # ── REML ─────────────────────────────────────────────────────────────────
  cat("  Running netmeta (REML)...\n")
  net_reml <- tryCatch(
    netmeta(TE = dat$TE, seTE = dat$seTE,
            treat1 = dat$t1, treat2 = dat$t2,
            studlab = dat$study,
            sm = sm, reference.group = reference,
            method.tau = "REML",
            comb.fixed = TRUE, comb.random = TRUE),
    error = function(e) {
      netmeta(TE = dat$TE, seTE = dat$seTE,
              treat1 = dat$t1, treat2 = dat$t2,
              studlab = dat$study,
              sm = sm, reference.group = reference,
              method.tau = "REML",
              common = TRUE, random = TRUE)
    }
  )

  tau2_reml <- net_reml$tau^2
  I2_reml   <- if (!is.null(net_reml$I2)) net_reml$I2 * 100 else NA
  Q_reml    <- if (!is.null(net_reml$Q)) net_reml$Q else NA

  # Extract REML treatment effects
  te_random_reml <- matrix(NA, nrow = n_trt, ncol = n_trt,
                           dimnames = list(treatments, treatments))
  se_random_reml <- te_random_reml
  lower_random_reml <- te_random_reml
  upper_random_reml <- te_random_reml
  lower_predict_reml <- te_random_reml
  upper_predict_reml <- te_random_reml

  for (i in seq_along(treatments)) {
    for (j in seq_along(treatments)) {
      if (i != j) {
        ti <- treatments[i]
        tj <- treatments[j]
        te_random_reml[ti, tj]    <- net_reml$TE.random[ti, tj]
        se_random_reml[ti, tj]    <- net_reml$seTE.random[ti, tj]
        lower_random_reml[ti, tj] <- net_reml$lower.random[ti, tj]
        upper_random_reml[ti, tj] <- net_reml$upper.random[ti, tj]
        if (!is.null(net_reml$lower.predict)) {
          lower_predict_reml[ti, tj] <- net_reml$lower.predict[ti, tj]
          upper_predict_reml[ti, tj] <- net_reml$upper.predict[ti, tj]
        }
      }
    }
  }

  # P-scores (REML)
  rank_reml <- tryCatch(
    netrank(net_reml, small.values = if (sm == "HR") "good" else "bad"),
    error = function(e) NULL
  )
  pscores_reml <- if (!is.null(rank_reml)) {
    if (!is.null(rank_reml$Pscore.random)) {
      as.list(rank_reml$Pscore.random)
    } else if (!is.null(rank_reml$ranking.random)) {
      as.list(rank_reml$ranking.random)
    } else {
      NULL
    }
  } else {
    NULL
  }

  results$reml <- list(
    tau2  = tau2_reml,
    tau   = net_reml$tau,
    I2    = I2_reml,
    Q     = Q_reml,
    TE_random  = as.data.frame(te_random_reml),
    seTE_random = as.data.frame(se_random_reml),
    lower_random = as.data.frame(lower_random_reml),
    upper_random = as.data.frame(upper_random_reml),
    lower_predict = as.data.frame(lower_predict_reml),
    upper_predict = as.data.frame(upper_predict_reml),
    pscores = pscores_reml
  )

  cat(sprintf("  REML: tau2=%.6f, I2=%.1f%%, Q=%.4f\n",
              tau2_reml, I2_reml, Q_reml))

  # ── HKSJ (Hartung-Knapp-Sidik-Jonkman) ──────────────────────────────────
  cat("  Running netmeta (HKSJ / hakn=TRUE)...\n")
  net_hksj <- tryCatch(
    netmeta(TE = dat$TE, seTE = dat$seTE,
            treat1 = dat$t1, treat2 = dat$t2,
            studlab = dat$study,
            sm = sm, reference.group = reference,
            method.tau = "DL",
            comb.fixed = TRUE, comb.random = TRUE,
            hakn = TRUE),
    error = function(e) {
      tryCatch(
        # Newer netmeta versions may use different parameter names
        netmeta(TE = dat$TE, seTE = dat$seTE,
                treat1 = dat$t1, treat2 = dat$t2,
                studlab = dat$study,
                sm = sm, reference.group = reference,
                method.tau = "DL",
                common = TRUE, random = TRUE,
                hakn = TRUE),
        error = function(e2) {
          cat(sprintf("    Warning: HKSJ netmeta failed: %s\n", e2$message))
          NULL
        }
      )
    }
  )

  if (!is.null(net_hksj)) {
    te_hksj <- matrix(NA, nrow = n_trt, ncol = n_trt,
                      dimnames = list(treatments, treatments))
    se_hksj <- te_hksj
    lower_hksj <- te_hksj
    upper_hksj <- te_hksj

    for (i in seq_along(treatments)) {
      for (j in seq_along(treatments)) {
        if (i != j) {
          ti <- treatments[i]
          tj <- treatments[j]
          te_hksj[ti, tj]    <- net_hksj$TE.random[ti, tj]
          se_hksj[ti, tj]    <- net_hksj$seTE.random[ti, tj]
          lower_hksj[ti, tj] <- net_hksj$lower.random[ti, tj]
          upper_hksj[ti, tj] <- net_hksj$upper.random[ti, tj]
        }
      }
    }

    results$hksj <- list(
      TE_random   = as.data.frame(te_hksj),
      seTE_random = as.data.frame(se_hksj),
      lower_random = as.data.frame(lower_hksj),
      upper_random = as.data.frame(upper_hksj)
    )
    cat("  HKSJ: extracted successfully\n")
  } else {
    results$hksj <- NULL
    cat("  HKSJ: skipped (not available)\n")
  }

  # ── Node-splitting (inconsistency test) ──────────────────────────────────
  cat("  Running netsplit (node-splitting)...\n")
  ns <- tryCatch(
    netsplit(net_dl),
    error = function(e) {
      cat(sprintf("    Warning: netsplit failed: %s\n", e$message))
      NULL
    }
  )

  if (!is.null(ns)) {
    # Extract comparison-level inconsistency p-values
    ns_results <- list()
    # netsplit returns a data frame with comparison, direct, indirect, etc.
    ns_df <- tryCatch({
      # Try to extract the main results
      if (is.data.frame(ns) || !is.null(ns$comparison)) {
        data.frame(
          comparison = ns$comparison,
          direct_TE  = ns$direct.random$TE,
          direct_se  = ns$direct.random$seTE,
          indirect_TE = ns$indirect.random$TE,
          indirect_se = ns$indirect.random$seTE,
          diff        = ns$compare.random$TE,
          diff_se     = ns$compare.random$seTE,
          diff_p      = ns$compare.random$p,
          stringsAsFactors = FALSE
        )
      } else {
        NULL
      }
    }, error = function(e) {
      cat(sprintf("    Warning: netsplit extraction failed: %s\n", e$message))
      NULL
    })

    if (!is.null(ns_df)) {
      results$node_splitting <- ns_df
      cat(sprintf("  Node-splitting: %d comparisons tested\n", nrow(ns_df)))
    } else {
      results$node_splitting <- list()
      cat("  Node-splitting: extraction failed\n")
    }
  } else {
    results$node_splitting <- list()
  }

  # ── Decomposition of Q (between-designs, within-designs) ─────────────────
  cat("  Extracting Q decomposition...\n")
  results$Q_decomposition <- list(
    Q_total      = if (!is.null(net_dl$Q)) net_dl$Q else NA,
    Q_df_total   = if (!is.null(net_dl$df.Q)) net_dl$df.Q else NA,
    Q_pval_total = if (!is.null(net_dl$pval.Q)) net_dl$pval.Q else NA,
    # Between-designs heterogeneity (inconsistency)
    Q_between    = if (!is.null(net_dl$Q.heterogeneity)) net_dl$Q.heterogeneity else NA,
    Q_between_df = if (!is.null(net_dl$df.Q.heterogeneity)) net_dl$df.Q.heterogeneity else NA,
    Q_between_p  = if (!is.null(net_dl$pval.Q.heterogeneity)) net_dl$pval.Q.heterogeneity else NA,
    # Within-designs (inconsistency Q)
    Q_inconsistency   = if (!is.null(net_dl$Q.inconsistency)) net_dl$Q.inconsistency else NA,
    Q_inconsistency_df = if (!is.null(net_dl$df.Q.inconsistency)) net_dl$df.Q.inconsistency else NA,
    Q_inconsistency_p  = if (!is.null(net_dl$pval.Q.inconsistency)) net_dl$pval.Q.inconsistency else NA
  )

  # ── League table (vs reference, random effects) ──────────────────────────
  cat("  Extracting league table vs reference...\n")
  league <- list()
  for (ti in treatments) {
    if (ti != reference) {
      league[[ti]] <- list(
        TE    = net_dl$TE.random[ti, reference],
        se    = net_dl$seTE.random[ti, reference],
        lower = net_dl$lower.random[ti, reference],
        upper = net_dl$upper.random[ti, reference]
      )
    }
  }
  results$league_vs_reference_dl <- league

  cat(sprintf("  Done: %s\n\n", dataset_id))
  return(results)
}


# ══════════════════════════════════════════════════════════════════════════════
# DATASET 1: Smoking Cessation (Hasselblad 1998) — from netmeta package
# ══════════════════════════════════════════════════════════════════════════════
cat("Loading smokingcessation dataset from netmeta...\n")
data(smokingcessation, package = "netmeta")

# smokingcessation has columns: event1, n1, event2, n2, treat1, treat2, studlab
# We need contrast-level TE and seTE (log-OR scale)
# Compute from 2x2 tables: logOR = log(e1*(n2-e2) / (e2*(n1-e1))), with 0.5 correction
smoking_dat <- data.frame(
  study = smokingcessation$studlab,
  t1    = as.character(smokingcessation$treat1),
  t2    = as.character(smokingcessation$treat2),
  stringsAsFactors = FALSE
)

# Use metafor to compute log-OR and SE from the 2x2 data
smoking_es <- escalc(measure = "OR",
                     ai = smokingcessation$event1,
                     n1i = smokingcessation$n1,
                     ci = smokingcessation$event2,
                     n2i = smokingcessation$n2,
                     data = smokingcessation)
smoking_dat$TE   <- as.numeric(smoking_es$yi)
smoking_dat$seTE <- sqrt(as.numeric(smoking_es$vi))

cat(sprintf("  Smoking: %d contrasts, %d unique studies\n",
            nrow(smoking_dat), length(unique(smoking_dat$study))))

smoking_results <- run_netmeta_analysis(
  dat = smoking_dat,
  sm = "OR",
  reference = "No contact",
  dataset_id = "smoking"
)


# ══════════════════════════════════════════════════════════════════════════════
# DATASET 2: CKD Nephroprotection (oncology_hr key — HR scale)
# 5 SGLT2i / MRA trials: CREDENCE, DAPA-CKD, EMPA-KIDNEY, FIDELIO-DKD, FIGARO-DKD
# Values match the HTML app's NMA_VALIDATION_DATASETS.oncology_hr exactly
# ══════════════════════════════════════════════════════════════════════════════
cat("Constructing oncology_hr (CKD Nephroprotection) dataset...\n")
oncology_dat <- data.frame(
  study = c("CREDENCE", "DAPA-CKD", "EMPA-KIDNEY", "FIDELIO-DKD", "FIGARO-DKD"),
  t1    = c("Canagliflozin", "Dapagliflozin", "Empagliflozin", "Finerenone", "Finerenone"),
  t2    = rep("Placebo", 5),
  TE    = c(-0.3567, -0.4943, -0.3285, -0.1985, -0.1278),
  seTE  = c(0.0847, 0.0882, 0.0639, 0.0617, 0.0857),
  stringsAsFactors = FALSE
)

oncology_results <- run_netmeta_analysis(
  dat = oncology_dat,
  sm = "HR",
  reference = "Placebo",
  dataset_id = "oncology_hr"
)


# ══════════════════════════════════════════════════════════════════════════════
# DATASET 3: Minimal (3 studies, 2 treatments) — pairwise OR
# ══════════════════════════════════════════════════════════════════════════════
cat("Constructing minimal dataset...\n")
minimal_dat <- data.frame(
  study = c("S1", "S2", "S3"),
  t1    = rep("Treatment", 3),
  t2    = rep("Control", 3),
  TE    = c(0.50, 0.55, 0.48),
  seTE  = c(0.25, 0.30, 0.28),
  stringsAsFactors = FALSE
)

minimal_results <- run_netmeta_analysis(
  dat = minimal_dat,
  sm = "OR",
  reference = "Control",
  dataset_id = "minimal"
)


# ══════════════════════════════════════════════════════════════════════════════
# DATASET 4: High Heterogeneity (8 studies, 3 treatments A/B/C)
# ══════════════════════════════════════════════════════════════════════════════
cat("Constructing high_het dataset...\n")
high_het_dat <- data.frame(
  study = c("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"),
  t1    = c("A", "A", "A", "B", "B", "B", "A", "A"),
  t2    = c("C", "C", "C", "C", "C", "C", "B", "B"),
  TE    = c(2.0, -0.5, 1.0, 1.5, -0.8, 0.3, 0.5, -0.5),
  seTE  = c(0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10),
  stringsAsFactors = FALSE
)

high_het_results <- run_netmeta_analysis(
  dat = high_het_dat,
  sm = "OR",
  reference = "C",
  dataset_id = "high_het"
)


# ══════════════════════════════════════════════════════════════════════════════
# DATASET 5: Multi-arm (2 three-arm studies, 4 treatments A/B/C/D)
# ══════════════════════════════════════════════════════════════════════════════
cat("Constructing multiarm dataset...\n")
multiarm_dat <- data.frame(
  study = c("MA1", "MA1", "MA1", "MA2", "MA2", "MA2"),
  t1    = c("A", "B", "A", "B", "C", "B"),
  t2    = c("D", "D", "B", "D", "D", "C"),
  TE    = c(0.6, 0.3, 0.3, 0.4, 0.7, -0.3),
  seTE  = c(0.25, 0.28, 0.30, 0.22, 0.26, 0.24),
  stringsAsFactors = FALSE
)

multiarm_results <- run_netmeta_analysis(
  dat = multiarm_dat,
  sm = "OR",
  reference = "D",
  dataset_id = "multiarm"
)


# ══════════════════════════════════════════════════════════════════════════════
# ASSEMBLE AND EXPORT
# ══════════════════════════════════════════════════════════════════════════════
output <- list(
  schema  = "frequentist_reference.v1",
  created = as.character(Sys.time()),
  R_version = R.version.string,
  packages = list(
    netmeta  = as.character(packageVersion("netmeta")),
    metafor  = as.character(packageVersion("metafor")),
    jsonlite = as.character(packageVersion("jsonlite"))
  ),
  datasets = list(
    smoking     = smoking_results,
    oncology_hr = oncology_results,
    minimal     = minimal_results,
    high_het    = high_het_results,
    multiarm    = multiarm_results
  )
)

# Write JSON
out_path <- file.path("R_validation", "frequentist_reference.json")
json_str <- toJSON(output, pretty = TRUE, auto_unbox = TRUE, na = "null",
                   digits = 8, force = TRUE)
writeLines(json_str, out_path)

cat(sprintf("\n=== DONE: wrote %s (%d bytes) ===\n",
            out_path, file.size(out_path)))

# ── Summary table ──────────────────────────────────────────────────────────────
cat("\n--- Summary ---\n")
cat(sprintf("  %-15s  tau2(DL)      tau2(REML)    I2(DL)   Q(DL)\n", "Dataset"))
cat(sprintf("  %-15s  ----------    ----------    ------   ------\n", ""))
for (nm in names(output$datasets)) {
  ds <- output$datasets[[nm]]
  cat(sprintf("  %-15s  %.6f      %.6f      %5.1f%%   %.2f\n",
              nm,
              ds$dl$tau2, ds$reml$tau2,
              ds$dl$I2, ds$dl$Q))
}
cat("\nAll datasets exported successfully.\n")
