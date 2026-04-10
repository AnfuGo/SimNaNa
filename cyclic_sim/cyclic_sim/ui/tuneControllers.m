function gains = tuneControllers(num_cell, den_cell, controller_type, method, wmin, wmax)
%#function pidtune
%#function looptune
%#function systune
%#function tunablePID

% ==============================
% Conversões iniciais
% ==============================

controller_type = upper(controller_type);
method = lower(method);

wc = [wmin wmax];

% ==============================
% Garante que entrada é cell
% ==============================

if ~iscell(num_cell)
    num_cell = {num_cell};
    den_cell = {den_cell};
end

n_systems = length(num_cell);

% ==============================
% Pré-aloca saída (struct array)
% ==============================

gains = cell(n_systems,1);

% ==============================
% Loop de sintonia
% ==============================

for i = 1:n_systems

    G = tf(num_cell{i}, den_cell{i});

    try

        % ===== PIDTUNE =====
        if strcmp(method, 'pidtune')

            C = pidtune(G, controller_type);

        % ===== LOOPTUNE =====
        elseif strcmp(method, 'looptune')

            if isempty(wc) || any(wc == 0)
                error('Faixa wc necessária para looptune');
            end

            Cblk = tunablePID('Cblk', lower(controller_type));
            [~, Ctuned] = looptune(G, Cblk, wc);
            C = getBlockValue(Ctuned, 'Cblk');

        else
            error('Método inválido');
        end

        % ===== Extrai ganhos =====
        Kp = C.Kp;

        if strcmp(controller_type, 'P')
            Ki = 0;
            Kd = 0;

        elseif strcmp(controller_type, 'PI')
            Ki = C.Ki;
            Kd = 0;

        elseif strcmp(controller_type, 'PID')
            Ki = C.Ki;
            Kd = C.Kd;

        else
            error('Tipo inválido');
        end

        % ===== Tempos equivalentes =====
        if Ki ~= 0
            Ti = Kp / Ki;
        else
            Ti = 0;
        end

        if Kd ~= 0
            Td = Kd / Kp;
        else
            Td = 0;
        end

        % ===== Struct de saída =====
        s.Kp = Kp;
        s.Ki = Ki;
        s.Kd = Kd;
        s.Ti = Ti;
        s.Td = Td;

        gains{i} = s;

    catch ME
        rethrow(ME)
    end
end

end