import os

file_path = r"c:\Users\Rishi\Desktop\trading_engins\mobile_app\src\screens\DashboardScreen.js"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """                        </View>
                    </View>
                </View>"""

replacement = """                        </View>
                        {agentStats?.sentiment && (
                            <View style={[styles.aiDecisionRow, { marginTop: 8, borderTopWidth: 0, paddingTop: 0 }]}>
                                <Text style={styles.aiDecisionLabel}>Market Sentiment:</Text>
                                <Text style={[
                                    styles.aiDecisionValue,
                                    { color: agentStats.sentiment.score > 0 ? colors.profit : agentStats.sentiment.score < 0 ? colors.loss : colors.textPrimary }
                                ]}>
                                    {agentStats.sentiment.label?.replace(/_/g, " ")}
                                </Text>
                                <Text style={styles.aiConfidence}>
                                    ({agentStats.sentiment.score > 0 ? "+" : ""}{agentStats.sentiment.score})
                                </Text>
                            </View>
                        )}
                    </View>
                </View>"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Success")
else:
    # Try with \r\n
    target_crlf = target.replace('\n', '\r\n')
    if target_crlf in content:
        content = content.replace(target_crlf, replacement.replace('\n', '\r\n'))
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Success with CRLF")
    else:
        print("Target not found")
