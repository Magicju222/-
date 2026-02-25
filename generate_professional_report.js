const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        HeadingLevel, AlignmentType, WidthType, BorderStyle, LevelFormat,
        Header, Footer, PageNumber } = require('docx');
const fs = require('fs');

// 模拟清洗后的数据
const reportData = {
    title: "公交运营数据分析报告",
    sheetName: "月分析表",
    summary: "本报告基于2024年1月公交运营数据，对线路收入、客运量、运营效率等关键指标进行全面分析。",
    keyInsights: [
        {
            insight: "248路运营总收入最高，达到64.08万元",
            dataSupport: "在所有线路中，248路的总收入显著高于其他线路",
            values: {
                "248路总收入": "64.08万元",
                "平均收入": "47.20万元",
                "高出平均": "35.8%"
            }
        },
        {
            insight: "激励类线路整体运营效率高于保障类线路",
            dataSupport: "激励类线路的车均收入普遍高于保障类线路",
            values: {
                "激励类车均收入": "9,834元",
                "保障类车均收入": "7,500元",
                "效率提升": "31.1%"
            }
        },
        {
            insight: "市场化收入占总收入比例平均为5.8%，有提升空间",
            dataSupport: "目前市场化收入占比较低，建议加强市场化运营",
            values: {
                "市场化收入占比": "5.8%",
                "行业平均水平": "15%",
                "提升潜力": "9.2%"
            }
        }
    ],
    tables: [
        {
            title: "运营收入排名（前10名）",
            headers: ["排名", "线路名称", "线路属性", "车辆数", "总收入(万元)", "车均收入(元)", "百公里收入(元)"],
            rows: [
                ["1", "248路", "激励", "33", "64.08", "19,417", "373.29"],
                ["2", "26路", "激励", "23", "58.11", "25,267", "460.07"],
                ["3", "9路", "激励", "20", "46.89", "23,446", "497.32"],
                ["4", "204路", "激励", "14", "33.48", "23,914", "511.05"],
                ["5", "5路", "激励", "14", "33.26", "23,759", "448.23"],
                ["6", "600路", "保障", "10", "25.03", "25,032", "504.00"],
                ["7", "804路", "保障", "4", "9.66", "24,150", "465.39"],
                ["8", "311路", "保障", "7", "9.52", "13,600", "298.24"],
                ["9", "221路", "品质", "6", "9.47", "15,783", "320.06"],
                ["10", "222路", "品质", "6", "9.44", "15,733", "318.04"]
            ]
        },
        {
            title: "属性分类汇总",
            headers: ["属性", "线路数", "车辆数", "配车占比(%)", "里程(万km)", "客运量(万人次)", "总收入(万元)", "车均收入(元)"],
            rows: [
                ["激励", "46", "530", "73.17", "1,353", "235.93", "851.04", "14,452"],
                ["保障", "23", "132", "18.23", "876.62", "110.91", "155.66", "9,934"],
                ["品质", "7", "4", "0.55", "7.36", "1.30", "3.28", "7,523"],
                ["新公交", "4", "0", "0.00", "6.95", "2.56", "0.03", "-"]
            ]
        }
    ]
};

// 创建文档
const doc = new Document({
    styles: {
        default: {
            document: {
                run: {
                    font: "微软雅黑",
                    size: 24  // 12pt
                }
            }
        },
        paragraphStyles: [
            {
                id: "Heading1",
                name: "Heading 1",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: { size: 36, bold: true, font: "微软雅黑", color: "2E74B5" },
                paragraph: { spacing: { before: 240, after: 120 } }
            },
            {
                id: "Heading2",
                name: "Heading 2",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: { size: 28, bold: true, font: "微软雅黑", color: "2E74B5" },
                paragraph: { spacing: { before: 200, after: 100 } }
            },
            {
                id: "Heading3",
                name: "Heading 3",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: { size: 24, bold: true, font: "微软雅黑" },
                paragraph: { spacing: { before: 160, after: 80 } }
            }
        ]
    },
    sections: [{
        properties: {
            page: {
                margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
            }
        },
        headers: {
            default: new Header({
                children: [new Paragraph({
                    children: [new TextRun({ text: "公交运营数据分析报告", bold: true, size: 20 })]
                })]
            })
        },
        footers: {
            default: new Footer({
                children: [new Paragraph({
                    children: [
                        new TextRun({ text: "第 ", size: 20 }),
                        new TextRun({ children: [PageNumber.CURRENT], size: 20 }),
                        new TextRun({ text: " 页", size: 20 })
                    ],
                    alignment: AlignmentType.CENTER
                })]
            })
        },
        children: [
            // 标题
            new Paragraph({
                text: reportData.title,
                heading: HeadingLevel.HEADING_1,
                alignment: AlignmentType.CENTER,
                spacing: { after: 200 }
            }),
            
            // 副标题
            new Paragraph({
                children: [
                    new TextRun({ text: `数据表：${reportData.sheetName}`, size: 24 })
                ],
                alignment: AlignmentType.CENTER,
                spacing: { after: 200 }
            }),
            
            // 生成时间
            new Paragraph({
                children: [
                    new TextRun({ text: `生成时间：${new Date().toLocaleString('zh-CN')}`, size: 20, color: "666666" })
                ],
                alignment: AlignmentType.CENTER,
                spacing: { after: 400 }
            }),
            
            // 报告摘要
            new Paragraph({
                text: "报告摘要",
                heading: HeadingLevel.HEADING_2,
                spacing: { before: 300, after: 150 }
            }),
            new Paragraph({
                children: [new TextRun(reportData.summary)],
                spacing: { after: 300 }
            }),
            
            // 关键洞察
            new Paragraph({
                text: "关键洞察",
                heading: HeadingLevel.HEADING_2,
                spacing: { before: 300, after: 150 }
            }),
            
            // 关键洞察列表
            ...reportData.keyInsights.flatMap((insight, index) => [
                new Paragraph({
                    children: [
                        new TextRun({ text: `${index + 1}. ${insight.insight}`, bold: true })
                    ],
                    spacing: { before: 200, after: 100 }
                }),
                new Paragraph({
                    children: [
                        new TextRun({ text: "数据支撑：", bold: true, size: 22 }),
                        new TextRun({ text: insight.dataSupport, size: 22 })
                    ],
                    indent: { left: 360 },
                    spacing: { after: 80 }
                }),
                new Paragraph({
                    children: [
                        new TextRun({ text: "具体数值：", bold: true, size: 22 })
                    ],
                    indent: { left: 360 },
                    spacing: { after: 60 }
                }),
                ...Object.entries(insight.values).map(([key, value]) => 
                    new Paragraph({
                        children: [
                            new TextRun({ text: `• ${key}：${value}`, size: 22 })
                        ],
                        indent: { left: 720 },
                        spacing: { after: 40 }
                    })
                )
            ]),
            
            // 数据表格
            new Paragraph({
                text: "数据明细",
                heading: HeadingLevel.HEADING_2,
                spacing: { before: 400, after: 200 }
            }),
            
            // 生成表格
            ...reportData.tables.flatMap(tableData => {
                const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
                const borders = { top: border, bottom: border, left: border, right: border };
                
                return [
                    // 表格标题
                    new Paragraph({
                        children: [new TextRun({ text: tableData.title, bold: true, size: 24 })],
                        spacing: { before: 300, after: 150 }
                    }),
                    
                    // 表格
                    new Table({
                        width: { size: 9360, type: WidthType.DXA },
                        columnWidths: Array(tableData.headers.length).fill(Math.floor(9360 / tableData.headers.length)),
                        rows: [
                            // 表头行
                            new TableRow({
                                children: tableData.headers.map(header => 
                                    new TableCell({
                                        borders,
                                        shading: { fill: "2E74B5", type: "clear" },
                                        children: [new Paragraph({
                                            children: [new TextRun({ text: header, bold: true, color: "FFFFFF", size: 20 })],
                                            alignment: AlignmentType.CENTER
                                        })]
                                    })
                                )
                            }),
                            // 数据行
                            ...tableData.rows.map(row => 
                                new TableRow({
                                    children: row.map(cell => 
                                        new TableCell({
                                            borders,
                                            children: [new Paragraph({
                                                children: [new TextRun({ text: String(cell), size: 20 })],
                                                alignment: AlignmentType.CENTER
                                            })]
                                        })
                                    )
                                })
                            )
                        ]
                    }),
                    
                    // 表格后空行
                    new Paragraph({ spacing: { after: 200 } })
                ];
            }),
            
            // 结语
            new Paragraph({
                text: "结语",
                heading: HeadingLevel.HEADING_2,
                spacing: { before: 400, after: 150 }
            }),
            new Paragraph({
                children: [
                    new TextRun("本报告基于清洗后的运营数据生成，数据准确可靠。建议根据关键洞察制定针对性的运营优化策略，提升整体运营效率。")
                ],
                spacing: { after: 200 }
            })
        ]
    }]
});

// 生成文档
Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync("professional_analysis_report.docx", buffer);
    console.log("✅ 专业分析报告已生成：professional_analysis_report.docx");
});
