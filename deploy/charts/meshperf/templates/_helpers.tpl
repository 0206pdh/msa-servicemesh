{{- define "meshperf.labels" -}}
app.kubernetes.io/part-of: meshperf
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | quote }}
{{- end }}
