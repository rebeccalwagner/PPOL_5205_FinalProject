# libraries 
library(dplyr)
library(stringr)
library(stm)
library(LDAvis)
library(htmlwidgets)
library(servr)
library(igraph)
library(ggraph)
library(tidyverse)

# set directory
setwd("/Users/rebeccawagner/Documents/Georgetown/25-26/Data Science/PPOL_5205_FinalProject")
# open data
bow_data <- read.csv("code/data/processed_text/bigrams_count_11_23.csv")
text_df <- read.csv("code/data/processed_text/text_df_11_23.csv")


# create correct data types for stm - this should do almost no preprocessing since my text data is already processed in python
processed <- textProcessor(
  documents = text_df$bigrams_str,
  metadata = NULL,
  lowercase = F,
  removestopwords = F,
  removenumbers = F,
  removepunctuation = F,
  stem = F,
  wordLengths = c(1, Inf)
)

out <- prepDocuments(processed$documents,
                     processed$vocab,
                     processed$meta,
                     lower.thresh = 0)

# Train model (with 10 topics same as python LDA)
stm_model <- stm(
  documents = out$documents,
  vocab     = out$vocab,
  K         = 10,
  max.em.its = 75,
  init.type = "Spectral"
)

# view topics
labelTopics(stm_model)

# view correlations

topic_cors <- topicCorr(stm_model)
cor_matrix <- topic_cors$cor

# Convert matrix to long format
cor_df <- as.data.frame(cor_matrix) %>%
  rownames_to_column("Topic1") %>%
  pivot_longer(-Topic1, names_to = "Topic2", values_to = "Correlation")

# Extract numeric topic numbers and convert to factors with proper ordering
cor_df$Topic1 <- factor(gsub("V", "", cor_df$Topic1), 
                        levels = 1:ncol(cor_matrix))
cor_df$Topic2 <- factor(gsub("V", "", cor_df$Topic2), 
                        levels = 1:ncol(cor_matrix))

# Create text labels
cor_df$label <- sprintf("%.2f", cor_df$Correlation)

# Plot
p <- ggplot(cor_df, aes(x = Topic1, y = Topic2, fill = Correlation)) +
  geom_tile() +
  geom_text(aes(label = label), size = 3) +
  scale_fill_gradient2(
    low = "red",
    mid = "white",
    high = "blue",
    midpoint = 0,
    limits = c(-0.3, 0.3),
    oob = scales::squish
  ) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(vjust = 0.5),
    axis.title.x = element_text(margin = margin(t=5)),
    panel.grid = element_blank()
  ) +
  labs(
    title = "Topic Correlation Heatmap",
    x = "Topic",
    y = "Topic",
    fill = "Corr"
  )

ggsave("topic_correlation_heatmap.png", plot = p, width = 8, height = 6, dpi = 300)


# LDAvis

#json <- stm::toLDAvis(stm_model, out$documents, out$vocab, R=30)

toLDAvis(
  mod = stm_model,
  docs = out$documents,
  R = 30  
)


# For more control and to save as HTML file:
# Extract necessary components from STM model
theta <- stm_model$theta  # document-topic distributions
phi <- exp(stm_model$beta$logbeta[[1]])  # topic-term distributions (convert from log scale)
vocab <- stm_model$vocab

# Clean phi: ensure no NAs, NaNs, or Infs, and rows sum to 1
phi[is.na(phi)] <- 0
phi[is.infinite(phi)] <- 0
phi <- phi + 1e-10  # add small constant to avoid zeros
phi <- phi / rowSums(phi)  # normalize rows to sum to 1

# Clean theta: ensure no NAs and rows sum to 1
theta[is.na(theta)] <- 0
theta <- theta + 1e-10
theta <- theta / rowSums(theta)

# Calculate document lengths (number of tokens per document)
doc_length <- sapply(out$documents, function(x) sum(x[2,]))

# Calculate term frequencies across all documents
term_frequency <- rep(0, length(vocab))
for (doc in out$documents) {
  term_frequency[doc[1,]] <- term_frequency[doc[1,]] + doc[2,]
}

# Ensure no zero frequencies (can cause issues)
term_frequency[term_frequency == 0] <- 1


# Create the LDAvis JSON object
json_vis <- createJSON(
  phi = phi,
  theta = theta,
  doc.length = doc_length,
  vocab = vocab,
  term.frequency = term_frequency,
  R = 30  # number of relevant terms to display for each topic
)


serVis(json_vis, 
       out.dir = "ldavis_output",
       open.browser = FALSE)

widget <- LDAvis::serVis(json, open.browser = FALSE)
htmlwidgets::saveWidget(widget, "lda_vis.html", selfcontained = TRUE)




