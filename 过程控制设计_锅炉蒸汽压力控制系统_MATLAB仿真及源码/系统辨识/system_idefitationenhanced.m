% (0.00, 0.04)
% (16.20, 1.36)
% (42.00, 3.48)
% (59.40, 4.72)
% (94.80, 6.80)
% (142.20, 9.48)
% (184.80, 11.48)
% (244.20, 13.56)
% (297.00, 15.07)
% (353.40, 16.61)
% (436.80, 18.09)
% (527.40, 19.29)
% (582.60, 19.97)
% (670.20, 20.80)
% (744.00, 21.37)
% (813.60, 21.64)
% (895.20, 22.01)
% (975.60, 22.28)
% (1054.80, 22.43)
% (1135.20, 22.69)
% (1207.80, 22.73)
% (1240.80, 22.81)
% 作者：周禄也 2025 04 30 
function simple_point_input_gui()
    % 初始化坐标数组
    X = [];
    Y = [];
    OP = 1;  % 初始 OP 值为 1
    enterCount = 0; % 回车次数计数器

    % 创建 GUI 窗口
    f = figure('Name', '输入数据点', 'Position', [500, 300, 650, 450], ...
               'NumberTitle', 'off', 'MenuBar', 'none', 'Resize', 'on');

    % 添加 X 输入框
    uicontrol('Style', 'text', 'Position', [40, 360, 200, 30], ...
              'String', '时间T(s)：', 'FontSize', 12, 'HorizontalAlignment', 'left');
    xEdit = uicontrol('Style', 'edit', 'Position', [170, 365, 100, 30], ...
                      'FontSize', 12, 'Callback', @editCallback);

    % 添加 Y 输入框
    uicontrol('Style', 'text', 'Position', [40, 310, 200, 30], ...
              'String', '液位高度(cm)：', 'FontSize', 12, 'HorizontalAlignment', 'left');
    yEdit = uicontrol('Style', 'edit', 'Position', [170, 315, 100, 30], ...
                      'FontSize', 12, 'Callback', @editCallback);

    % 添加 OP 输入框
    uicontrol('Style', 'text', 'Position', [40, 260, 100, 30], ...
              'String', '水泵 OP：', 'FontSize', 12, 'HorizontalAlignment', 'left');
    opEdit = uicontrol('Style', 'edit', 'Position', [100, 265, 150, 30], ...
                       'FontSize', 12, 'String', '1');

    uicontrol('Style', 'pushbutton', 'String', '设定 OP', ...
              'Position', [260, 265, 90, 30], 'FontSize', 12, ...
              'Callback', @setOP);

    % 信息提示
    infoText = uicontrol('Style', 'text', 'Position', [40, 220, 330, 30], ...
                         'String', '等待输入...', 'FontSize', 12, ...
                         'HorizontalAlignment', 'center');

    % 添加按钮：添加点
    uicontrol('Style', 'pushbutton', 'String', '添加点', ...
              'Position', [40, 150, 100, 40], 'FontSize', 12, ...
              'Callback', @addPoint);

    % 添加按钮：计算
    uicontrol('Style', 'pushbutton', 'String', '计算', ...
              'Position', [155, 150, 100, 40], 'FontSize', 12, ...
              'Callback', @calculateFit);

    % 添加按钮：退出
    uicontrol('Style', 'pushbutton', 'String', '退出', ...
              'Position', [270, 150, 100, 40], 'FontSize', 12, ...
              'Callback', @(src, event) close(f));

    % 显示输入的数据点的表格区域
    uicontrol('Style', 'text', 'Position', [400, 400, 200, 30], ...
              'String', '已输入数据点:', 'FontSize', 12, 'HorizontalAlignment', 'left');
    dataTable = uitable('Position', [400, 175, 220, 220], ...
                        'ColumnName', {'X', 'Y'}, ...
                        'RowName', [], 'FontSize', 12);

    % 显示传递函数输出的文本框
    uicontrol('Style', 'text', 'Position', [200, 95, 300, 30], ...
              'String', '一阶开环传递函数:', 'FontSize', 18, 'HorizontalAlignment', 'left');
    tfOutput = uicontrol('Style', 'edit', 'Position', [20, 10, 600, 80], ...
                         'FontSize', 18, 'HorizontalAlignment', 'center', 'Enable', 'inactive');

    % 编辑框回调：处理回车事件
    function editCallback(~, ~)
        enterCount = enterCount + 1;
        if enterCount == 1
            uicontrol(yEdit); % 第一次按回车，聚焦到 Y 输入框
        elseif enterCount == 2
            addPoint(); % 第二次按回车，执行添加点操作
            enterCount = 0; % 重置回车计数器
        end
    end

    % 添加点的回调
    function addPoint(~, ~)
        xStr = get(xEdit, 'String');
        yStr = get(yEdit, 'String');
        xVal = str2double(xStr);
        yVal = str2double(yStr);

        if isnan(xVal) || isnan(yVal)
            set(infoText, 'String', '⚠️ 无效输入，请输入数字');
            return;
        end

        X(end+1) = xVal;
        Y(end+1) = yVal;

        % 更新数据点表格
        set(dataTable, 'Data', [X(:), Y(:)]);

        % 清空输入框并回到X输入框
        set(xEdit, 'String', '');
        set(yEdit, 'String', '');
        uicontrol(xEdit);  % 将焦点设回X框

        set(infoText, 'String', sprintf('✅ 已添加点 (%.2f, %.2f)，共 %d 个点', xVal, yVal, length(X)));
    end

    % 设置 OP 的回调
    function setOP(~, ~)
        val = str2double(get(opEdit, 'String'));
        if isnan(val) || val <= 0
            set(infoText, 'String', '⚠️ OP值无效，请输入正数');
        else
            OP = val;
            set(infoText, 'String', sprintf('✅ 当前 OP = %.2f', OP));
        end
    end

    % 计算拟合
    function calculateFit(~, ~)
        if length(X) < 3
            set(infoText, 'String', '⚠️ 至少需要 3 个点才能拟合');
            return;
        end

        % 拟合一阶系统模型
        fit_type = fittype('K * (1 - exp(-x / tau))', ...
                           'independent', 'x', 'dependent', 'y');
        initial_guess = [max(Y), mean(X)];
        [fit_result, gof] = fit(X(:), Y(:), fit_type, 'StartPoint', initial_guess);

        % 输出传递函数数值
        K = fit_result.K; 
        tau = fit_result.tau;
        G = K / (tau + 1); % 计算传递函数数值

        % 输出传递函数
        tfStr = sprintf('G(s) = %.2f / (%.2fs + 1)', K, tau);
        set(tfOutput, 'String', tfStr);

        % 输出结果
        disp('—— 拟合结果 ——');
        disp(['原始拟合 K = ', num2str(fit_result.K)]);
        disp(['τ = ', num2str(tau)]);
        disp(['传递函数 G(s) = ', num2str(K), ' / (', num2str(tau), 's + 1)']);
        disp(['传递函数数值 = ', num2str(G)]);

        % 绘图：不考虑 OP 值
        figure;
        plot(X, Y, 'bo', 'MarkerFaceColor', 'b');
        hold on;
        x_fit = linspace(min(X), max(X), 1000);
        y_fit = K * (1 - exp(-x_fit / tau));
        plot(x_fit, y_fit, 'r-', 'LineWidth', 2);
        title('一阶系统阶跃响应拟合', 'FontSize', 14);
        xlabel('时间 (X)', 'FontSize', 12);
        ylabel('响应 (Y)', 'FontSize', 12);
        legend({'原始数据', '拟合曲线'}, 'FontSize', 12);
        grid on;

        % 输出信息
        set(infoText, 'String', '✅ 拟合完成（已计算传递函数数值），结果见图和命令行');
    end
end
