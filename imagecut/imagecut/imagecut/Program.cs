using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Drawing.Pens;
using SixLabors.Primitives;
using SixLabors.Shapes;

namespace imagecut
{
    class KeyInfo
    {

        public KeyInfo(string name)
        {
            Name = name;
            WidthMultiplier = 1.0f;
            XGapMultiplier = 1.0f;
            HeightGapMultiplier = 1.0f;
        }

        public string Name { get; set;}
        public float WidthMultiplier { get; set; }
        public float XGapMultiplier { get; set; }
        public float HeightGapMultiplier { get; set; }
    }

    public class LayoutInfo
    {
        public string Name { get; set; }
        public float Scale { get; set; }
        public float StartHeight { get; set; }
        public float KeyWidth { get; set; }
    }

    class Program
    {
        static void Main(string[] args)
        {
            var layoutsNames = new[]
            {
                new LayoutInfo()
                {
                    Name = "photoshop",
                    Scale = 1.688f,
                    StartHeight = 420f,
                    KeyWidth = 108.8f
                },
                new LayoutInfo()
                {
                    Name = "premiere",
                    Scale = 1.740f,
                    StartHeight = 421f,
                    KeyWidth = 106.9f
                },
                new LayoutInfo()
                {
                    Name = "standard",
                    Scale = 1.688f,
                    StartHeight = 420f,
                    KeyWidth = 108.8f
                },
                new LayoutInfo()
                {
                    Name = "standard_lc",
                    Scale = 1.688f,
                    StartHeight = 420f,
                    KeyWidth = 108.8f
                }
            };

            var layoutsNamesToProcess = new[]
            {
                "photoshop",
                "premiere",
                "standard",
                "standard_lc"
            };

            var layoutsToProcess = layoutsNames
                .Where(x => layoutsNamesToProcess.Contains(x.Name)).ToList();

            var basePath = "C:\\repo\\rpigfx\\keysets\\";
            var extension = ".png";

            bool saveKeys = true;

            const float gapAfterHKeyRow1 = 2.3f;
            const float gapAfterHKeyNormal = 2.3f;
            const float row1xgap = 1.165f;
            
            foreach (var layout in layoutsToProcess)
            {
                float scale = layout.Scale;
                float keyheight = 107 * scale;
                float keywidth = layout.KeyWidth * scale;
                float keyspacingvertical = 30 * scale;
                float keyspacinghorizontal = 31.3f * scale;
                float startHeight = layout.StartHeight * scale;
                float startWidth = 62 * scale;

                var workingDir = basePath + layout.Name + "\\";
                var masterImage = File.OpenRead(workingDir + layout.Name + extension);
                var img = Image.Load(masterImage);

                KeyInfo[][] keyInfos = {
                    new[]
                    {
                        new KeyInfo("h1") {XGapMultiplier = gapAfterHKeyRow1},
                        new KeyInfo("esc") {XGapMultiplier = row1xgap },
                        new KeyInfo("f1") {XGapMultiplier = row1xgap},
                        new KeyInfo("f2") {XGapMultiplier = row1xgap},
                        new KeyInfo("f3") {XGapMultiplier = row1xgap},
                        new KeyInfo("f4") {XGapMultiplier = row1xgap},
                        new KeyInfo("f5") {XGapMultiplier = row1xgap},
                        new KeyInfo("f6") {XGapMultiplier = row1xgap},
                        new KeyInfo("f7") {XGapMultiplier = row1xgap},
                        new KeyInfo("f8") {XGapMultiplier = row1xgap},
                        new KeyInfo("f9") {XGapMultiplier = row1xgap},
                        new KeyInfo("f10") {XGapMultiplier = row1xgap},
                        new KeyInfo("f11") {XGapMultiplier = row1xgap},
                        new KeyInfo("f12") {XGapMultiplier = row1xgap},
                        new KeyInfo("power") {XGapMultiplier = row1xgap}
                    },
                    new[]
                    {
                        new KeyInfo("h2"){XGapMultiplier = gapAfterHKeyNormal, HeightGapMultiplier = 1.2f},
                        new KeyInfo("tilde") {},
                        new KeyInfo("1"),
                        new KeyInfo("2"),
                        new KeyInfo("3"),
                        new KeyInfo("4"),
                        new KeyInfo("5"),
                        new KeyInfo("6"),
                        new KeyInfo("7"),
                        new KeyInfo("8"),
                        new KeyInfo("9"),
                        new KeyInfo("0"),
                        new KeyInfo("minus"),
                        new KeyInfo("plus") {XGapMultiplier = 1.2f},
                        new KeyInfo("delete") {WidthMultiplier = 1.52f}
                    },
                    new[]
                    {
                        new KeyInfo("h3"){XGapMultiplier = gapAfterHKeyNormal,  HeightGapMultiplier = 1.2f},
                        new KeyInfo("tab")
                        {
                            WidthMultiplier = 1.45f,
                            XGapMultiplier = 1.65f,
                           
                        },
                        new KeyInfo("q"),
                        new KeyInfo("w"),
                        new KeyInfo("e"),
                        new KeyInfo("r"),
                        new KeyInfo("t"),
                        new KeyInfo("y"),
                        new KeyInfo("u"),
                        new KeyInfo("i"),
                        new KeyInfo("o"),
                        new KeyInfo("p"),
                        new KeyInfo("leftsquarebracket"),
                        new KeyInfo("rightsquarebracket"),
                        new KeyInfo("backslash")
                    },
                    new[]
                    {
                        new KeyInfo("h4"){XGapMultiplier = gapAfterHKeyNormal, HeightGapMultiplier = 1.38f},
                        new KeyInfo("capslock")
                        {
                            WidthMultiplier = 1.65f,
                            XGapMultiplier = 2.6f,
                            
                        },
                        new KeyInfo("a"),
                        new KeyInfo("s"),
                        new KeyInfo("d"),
                        new KeyInfo("f"),
                        new KeyInfo("g"),
                        new KeyInfo("h"),
                        new KeyInfo("j"),
                        new KeyInfo("k"),
                        new KeyInfo("l"),
                        new KeyInfo(";"),
                        new KeyInfo("singlequote") {XGapMultiplier = 1.6f},
                        new KeyInfo("return") {WidthMultiplier = 1.63f}
                    },
                    new[]
                    {
                        new KeyInfo("h5"){XGapMultiplier = gapAfterHKeyNormal,  HeightGapMultiplier = 1.2f},
                        new KeyInfo("leftshift")
                        {
                            WidthMultiplier = 1.45f,
                            XGapMultiplier = 1.65f,
                        },
                        new KeyInfo("bottomleft"),
                        new KeyInfo("z"),
                        new KeyInfo("x"),
                        new KeyInfo("c"),
                        new KeyInfo("v"),
                        new KeyInfo("b"),
                        new KeyInfo("n"),
                        new KeyInfo("m"),
                        new KeyInfo("comma"),
                        new KeyInfo("dot"),
                        new KeyInfo("forwardslash"),
                        new KeyInfo("up"),
                        new KeyInfo("rightshift")
                    },
                    new[]
                    {
                        new KeyInfo("h6"){XGapMultiplier = gapAfterHKeyNormal},
                        new KeyInfo("leftfn"),
                        new KeyInfo("leftcontrol"),
                        new KeyInfo("leftalt"),
                        new KeyInfo("leftcommand") {XGapMultiplier = 1.2f},
                        new KeyInfo("space") {WidthMultiplier = 6.7f, XGapMultiplier = 1.2f},
                        new KeyInfo("rightcommand"),
                        new KeyInfo("rightalt"),
                        new KeyInfo("left"),
                        new KeyInfo("down"),
                        new KeyInfo("right")
                    }
                };

                List<RectangleF> rects = new List<RectangleF>();
                
                int rowNum = 0;
                foreach (var row in keyInfos)
                {
                    int keyInColumn = 0;
                    var prevWidth = startWidth + row.Take(keyInColumn).Sum(x =>
                                        (keywidth) + keyspacinghorizontal);
                    var xPoint = prevWidth;
                    var yPoint = startHeight + keyInfos.Take(rowNum)
                                     .Sum(y => keyheight + y.First().HeightGapMultiplier *
                                               keyspacingvertical); //rowNum * (keyheight + keyspacingvertical);
                    var rect = new RectangleF(xPoint, yPoint, keywidth, keyheight);
                    var clone = img.Clone();
                    clone.Mutate(x =>
                        x.Crop(new Rectangle((int)rect.Left, (int)rect.Top, (int)rect.Width, (int)rect.Height)));

                    if (saveKeys)
                    {
                        clone.SaveAsPng(File.OpenWrite(workingDir + rowNum + "_" + keyInColumn + ".png"));
                        clone.SaveAsPng(File.OpenWrite(workingDir + rowNum + "_" + keyInColumn + "_shift.png"));
                    }

                    rects.Add(rect);
                    var initOffset = keywidth + keyspacinghorizontal * 2;
                    
                    foreach (var key in row)
                    {
                        prevWidth = startWidth + row.Take(keyInColumn).Sum(x =>
                                        (x.WidthMultiplier * keywidth) + (x.XGapMultiplier * keyspacinghorizontal));
                        xPoint = prevWidth;
                        yPoint = startHeight + keyInfos.Take(rowNum).Sum(y =>
                                     keyheight + y.First().HeightGapMultiplier *
                                     keyspacingvertical); //rowNum * (keyheight + keyspacingvertical);
                        rect = new RectangleF(xPoint, yPoint, keywidth * key.WidthMultiplier, keyheight);
                        var r = new RectangularePolygon(rect);

                        if (saveKeys)
                        {
                            clone = img.Clone();
                            clone.Mutate(x =>
                                x.Crop(new Rectangle((int) rect.Left, (int) rect.Top, (int) rect.Width,
                                    (int) rect.Height)));
                            clone.SaveAsPng(File.OpenWrite(workingDir + rowNum + "_" + (keyInColumn + 1) + ".png"));
                            clone.SaveAsPng(
                                File.OpenWrite(workingDir + rowNum + "_" + (keyInColumn + 1) + "_shift.png"));
                        }

                        keyInColumn++;
                        img.Mutate(x => x.Draw(new Pen<Rgba32>(Rgba32.Red, 1), r));

                        // compensate for not having first key
                        rect.X = rect.X + initOffset;

                        rects.Add(rect);
                    }

                    rowNum++;
                }

                img.SaveAsPng(File.OpenWrite(workingDir + "out.png"));
                if (File.Exists(workingDir + "out.txt"))
                {
                    File.Delete(workingDir + "out.txt");
                }

                File.WriteAllLines(workingDir + "out.txt",
                    rects.Select(x =>
                        $"{Math.Round(x.X)},{Math.Round(x.Y)},{Math.Round(x.Width)},{Math.Round(x.Height)}"));

            }
        }
    }
}
