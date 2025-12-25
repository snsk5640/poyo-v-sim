//=====================================================================
//  testbench.v (Fixed for poyo-v-sim pipeline_3stage)
//=====================================================================
`timescale 1ns/1ps
`include "define.vh"

module testbench;

    //-----------------------------------------------------------------
    //  クロック・リセット
    //-----------------------------------------------------------------
    reg clk = 0;
    reg rst = 1;

    //-----------------------------------------------------------------
    //  周辺 I/O
    //-----------------------------------------------------------------
    reg        uart_rx = 1;
    reg  [3:0] gpi_in  = 0;
    wire       uart_tx;
    wire [3:0] gpo_out;

    //-----------------------------------------------------------------
    //  50 MHz クロック (STEP=20ns)
    //-----------------------------------------------------------------
    localparam STEP = 1000000;

    always begin
        #(STEP/2) clk = ~clk;
    end

    //-----------------------------------------------------------------
    //  DUT (Device Under Test)
    //-----------------------------------------------------------------
    cpu_top dut (
        .clk     (clk),
        .rst     (rst),
        .uart_rx (uart_rx),
        .gpi_in  (gpi_in),
        .gpo_out (gpo_out),
        .uart_tx (uart_tx)
    );

    //-----------------------------------------------------------------
    //  波形出力 (GTKWave用)
    //-----------------------------------------------------------------
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, testbench);
    end

    //-----------------------------------------------------------------
    //  DUT 内部信号の参照 (cpu_top.v の信号名に合わせて修正済み)
    //-----------------------------------------------------------------
    
    // プログラムカウンタ (Fetch Stage)
    wire [31:0] imem_addr    = dut.imem_addr;
    
    // 命令コード (Fetch Stage)
    wire [31:0] imem_rd_data = dut.imem_rd_data;
    
    // データメモリアドレス (Execution Stage)
    wire [31:0] dmem_addr    = dut.dmem_addr;
    
    // データメモリ書込データ (Execution Stage: ストアする値)
    wire [31:0] dmem_wr_data = dut.ex_store_value;
    
    // データメモリ書込許可 (Execution Stage: 4bit)
    wire  [3:0] dmem_we      = dut.dmem_we;

    // データメモリ読出データ (Write-Back Stage: ロードされた値)
    // ※cpu_top内ではbyteごとに分かれているため、統合後の wb_load_value を参照します
    wire [31:0] dmem_rd_data = dut.wb_load_value;


    //-----------------------------------------------------------------
    //  シミュレーション制御
    //-----------------------------------------------------------------
    initial begin
        clk = 0;
        rst = 1;
        
        // リセットシーケンス
        #(STEP*2);
        rst = 0;

        // 実行時間（必要に応じて調整してください）
        #(STEP * 5000);
        
        $display("--- Simulation Timeout ---");
        $finish;
    end

    //-----------------------------------------------------------------
    //  STIL 向けベクタ出力 & CSV出力
    //-----------------------------------------------------------------
    integer stil_file;
    integer inst_file;
    integer csv_file;
    reg [70:0] pi_vec;
    reg [104:0] po_vec;

    initial begin
        stil_file = $fopen("output_vectors.txt", "w");
        inst_file = $fopen("inst_rslt.hex", "w");
        csv_file  = $fopen("trace.csv", "w");

        if (csv_file) begin
             $fdisplay(csv_file, "cycle,clk,rst,imem_addr,imem_rd_data,dmem_we,dmem_addr,dmem_rd_data");
        end
    end

    //-----------------------------------------------------------------
    //  モニタリング処理
    //-----------------------------------------------------------------
    integer cycle_cnt = 0;

    always @(posedge clk) begin
        cycle_cnt <= cycle_cnt + 1;

        // 画面表示 (100サイクルごとに表示)
        if (cycle_cnt % 100 == 0) begin
             $display("Time: %t, Cycle: %d, PC: %h, Inst: %h", $time, cycle_cnt, imem_addr, imem_rd_data);
        end

        // CSV出力
        if (csv_file) begin
            $fdisplay(csv_file, "%d,%b,%b,%h,%h,%b,%h,%h",
                      cycle_cnt, clk, rst, imem_addr, imem_rd_data, dmem_we, dmem_addr, dmem_rd_data);
        end

        // STIL出力
        pi_vec = {clk, rst, uart_rx, gpi_in, imem_rd_data, dmem_rd_data};
        po_vec = {gpo_out, uart_tx, imem_addr, dmem_addr, dmem_we, dmem_wr_data};
        
        $fdisplay(stil_file, "\"_pi\"=%071b;",  pi_vec);
        $fdisplay(stil_file, "\"_po\"=%0105b;", po_vec);
        
        // 命令ログ
        $fdisplay(inst_file, "%08h", imem_rd_data);
    end

endmodule
