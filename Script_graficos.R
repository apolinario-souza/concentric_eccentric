# ==========================================================
# Gráficos Familiarização + Retenção
# - Média ± EP
# - Sem grade
# - Sem linha ligando B4 à Retenção
# - Uma figura para cada variável dependente
# ==========================================================

library(readxl)
library(dplyr)
library(ggplot2)

# Ler dados
dados <- read_excel("dados.xlsx")

# Variáveis dependentes
vars <- c(
  "TR_mean","TR_sd","TR_cv",
  "TM_mean","TM_sd","TM_cv",
  "EA_mean","EA_sd","EA_cv",
  "EC_mean","EC_sd","EC_cv",
  "PV_mean","PV_sd","PV_cv",
  "ETA_mean","ETA_sd","ETA_cv",
  "ETC_mean","ETC_sd","ETC_cv"
)

# Ajustar fatores
dados <- dados %>%
  mutate(
    bloco_plot = case_when(
      fase == "familiarizacao" & bloco == 1 ~ "B1",
      fase == "familiarizacao" & bloco == 2 ~ "B2",
      fase == "familiarizacao" & bloco == 3 ~ "B3",
      fase == "familiarizacao" & bloco == 4 ~ "B4",
      fase == "retencao" ~ "Retenção"
    ),
    
    bloco_plot = factor(
      bloco_plot,
      levels = c("B1", "B2", "B3", "B4", "Retenção")
    ),
    
    acao = factor(
      acao,
      levels = c("con", "exc"),
      labels = c("Concentrico", "Excentrico")
    )
  )

# Criar pasta para salvar figuras
dir.create("Figuras", showWarnings = FALSE)

# ==========================================================
# Loop para todas as variáveis
# ==========================================================

for(v in vars){
  
  resumo <- dados %>%
    filter(!is.na(bloco_plot)) %>%
    group_by(acao, bloco_plot) %>%
    summarise(
      media = mean(.data[[v]], na.rm = TRUE),
      sd = sd(.data[[v]], na.rm = TRUE),
      n = sum(!is.na(.data[[v]])),
      se = sd / sqrt(n),
      .groups = "drop"
    )
  
  # Dados apenas da familiarização
  resumo_fam <- resumo %>%
    filter(bloco_plot %in% c("B1","B2","B3","B4"))
  
  # Dados da retenção
  resumo_ret <- resumo %>%
    filter(bloco_plot == "Retenção")
  
  p <- ggplot() +
    
    # Linha apenas na familiarização
    geom_line(
      data = resumo_fam,
      aes(
        x = bloco_plot,
        y = media,
        color = acao,
        group = acao
      ),
      linewidth = 1.2
    ) +
    
    # Pontos da familiarização
    geom_point(
      data = resumo_fam,
      aes(
        x = bloco_plot,
        y = media,
        color = acao,
        shape = acao
      ),
      size = 3.5
    ) +
    
    # Pontos da retenção
    geom_point(
      data = resumo_ret,
      aes(
        x = bloco_plot,
        y = media,
        color = acao,
        shape = acao
      ),
      size = 3.5
    ) +
    
    # Barras de erro
    geom_errorbar(
      data = resumo,
      aes(
        x = bloco_plot,
        y = media,
        ymin = media - se,
        ymax = media + se,
        color = acao
      ),
      width = 0.12,
      linewidth = 0.8
    ) +
    
    labs(
      title = v,
      x = "Blocos",
      y = NULL,
      color = "",
      shape = ""
    ) +
    
    theme_classic(base_size = 14) +
    
    theme(
      plot.title = element_text(
        hjust = 0.5,
        face = "bold",
        size = 18
      ),
      axis.text.x = element_text(
        angle = 45,
        hjust = 1
      ),
      legend.position = "top",
      legend.title = element_blank()
    )
  
  print(p)
  
  ggsave(
    filename = paste0("Figuras/", v, ".png"),
    plot = p,
    width = 8,
    height = 5,
    dpi = 300
  )
}

# ==========================================================
# Fim
# Todas as figuras estarão na pasta "Figuras"
# ==========================================================