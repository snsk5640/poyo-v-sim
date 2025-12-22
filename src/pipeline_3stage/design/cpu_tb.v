//
// cpu_tb (Updated for Icarus Verilog)
//

module cpu_tb;

    reg clk;
    reg rst;

    parameter CYCLE = 10;

    // クロック生成
    always #(CYCLE/2) clk = ~clk;

    // CPUコアのインスタンス化
    cpu_top cpu_top (
       .clk(clk),
       .rst(rst)
    );

    // リセット動作
    initial begin
        #10 clk = 1'd0;
        rst = 1'd1;
        #(CYCLE) rst = 1'd0;
    end

    // --- 追加部分: シミュレーション制御と波形出力 ---
    initial begin
        // 波形ファイルの指定
        $dumpfile("wave.vcd");
        // cpu_tb以下の全信号を記録
        $dumpvars(0, cpu_tb);

        // シミュレーション実行時間（200,000単位時間待ってから終了）
        // ※プログラムが長い場合はこの数値を増やしてください
        #200000;
        
        $display("--- Simulation Timeout (Finished) ---");
        $finish; // シミュレータを強制終了
    end

endmodule
